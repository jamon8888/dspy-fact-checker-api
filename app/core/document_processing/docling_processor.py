"""
Docling-based document processor for advanced document processing.
"""

import logging
import asyncio
import io
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime
import tempfile
import os

from app.core.document_processing.base import (
    DocumentProcessor, ProcessingResult, DocumentType, ProcessingMethod,
    DocumentMetadata, TableData, ImageData, StructuredContent
)
from app.core.document_processing.exceptions import (
    ProcessingError, UnsupportedFormatError, CorruptedDocumentError,
    ProcessingTimeoutError, ExtractionError, ConfigurationError
)

logger = logging.getLogger(__name__)

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.datamodel.document import DoclingDocument
    DOCLING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Docling not available: {e}")
    DOCLING_AVAILABLE = False
    DocumentConverter = None
    InputFormat = None
    PdfPipelineOptions = None
    DoclingDocument = None


class DoclingConfiguration:
    """Configuration for Docling document processing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Docling configuration."""
        self.config = config or {}
        
        # PDF processing options
        self.pdf_options = self._create_pdf_options()
        
        # Word document options
        self.docx_options = self._create_docx_options()
        
        # General options
        self.max_pages = self.config.get("max_pages", 1000)
        self.timeout_seconds = self.config.get("timeout_seconds", 300)
        self.extract_images = self.config.get("extract_images", True)
        self.extract_tables = self.config.get("extract_tables", True)
        self.do_ocr = self.config.get("do_ocr", False)  # We'll use Mistral OCR separately
        
    def _create_pdf_options(self) -> Optional[Any]:
        """Create PDF pipeline options."""
        if not DOCLING_AVAILABLE:
            return None
            
        return PdfPipelineOptions(
            # OCR settings - disabled as we'll use Mistral OCR
            do_ocr=self.config.get("do_ocr", False),
            
            # Table extraction settings
            do_table_structure=self.config.get("extract_tables", True),
            table_structure_options={
                "do_cell_matching": True,
                "mode": "accurate"
            },
            
            # Image extraction settings
            do_picture_extraction=self.config.get("extract_images", True),
            picture_extraction_options={
                "do_figure_extraction": True,
                "do_image_extraction": True,
                "min_figure_size": (50, 50),
                "extract_image_metadata": True,
                "image_classification": True
            },
            
            # Layout analysis settings
            do_layout_analysis=True,
            layout_analysis_options={
                "detect_headers": True,
                "detect_footers": True,
                "detect_columns": True,
                "reading_order_detection": True,
                "paragraph_detection": True
            }
        )
    
    def _create_docx_options(self) -> Dict[str, Any]:
        """Create Word document processing options."""
        return {
            "extract_images": self.config.get("extract_images", True),
            "extract_tables": self.config.get("extract_tables", True),
            "preserve_formatting": True,
            "extract_comments": True,
            "extract_footnotes": True
        }


class DoclingProcessor(DocumentProcessor):
    """Advanced document processor using Docling."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Docling processor."""
        super().__init__(config)
        
        if not DOCLING_AVAILABLE:
            raise ConfigurationError("Docling is not available. Please install docling>=2.36.0")
        
        self.docling_config = DoclingConfiguration(config)
        self.converter = self._create_converter()
        
    def _create_converter(self) -> DocumentConverter:
        """Create and configure Docling document converter."""
        try:
            format_options = {}
            
            # Add PDF options
            if self.docling_config.pdf_options:
                format_options[InputFormat.PDF] = self.docling_config.pdf_options
            
            # Add Word document options (only DOCX is supported by Docling)
            format_options[InputFormat.DOCX] = self.docling_config.docx_options
            
            return DocumentConverter(format_options=format_options)
            
        except Exception as e:
            raise ConfigurationError(f"Failed to create Docling converter: {str(e)}")
    
    def supports_format(self, file_type: DocumentType) -> bool:
        """Check if processor supports the given format."""
        supported = {
            DocumentType.PDF,
            DocumentType.DOCX,
            # Note: DOC format is not supported by Docling, only DOCX
        }
        return file_type in supported

    def get_supported_formats(self) -> List[DocumentType]:
        """Get list of supported document formats."""
        return [
            DocumentType.PDF,
            DocumentType.DOCX,
            # Note: DOC format is not supported by Docling, only DOCX
        ]
    
    async def process_document(
        self, 
        file_data: Union[bytes, BinaryIO], 
        file_type: DocumentType,
        filename: Optional[str] = None,
        **kwargs
    ) -> ProcessingResult:
        """
        Process document using Docling.
        
        Args:
            file_data: Document data as bytes or file-like object
            file_type: Type of document to process
            filename: Original filename (optional)
            **kwargs: Additional processing options
            
        Returns:
            ProcessingResult with extracted content and metadata
        """
        start_time = datetime.now()
        
        try:
            # Validate input
            self.validate_input(file_data, file_type, self.config.get("max_file_size"))
            
            # Convert file data to bytes if needed
            if isinstance(file_data, bytes):
                data_bytes = file_data
            else:
                data_bytes = file_data.read()
            
            # Get input format for Docling
            input_format = self._get_input_format(file_type)
            
            # Process document with timeout
            docling_result = await asyncio.wait_for(
                self._process_with_docling(data_bytes, input_format, filename),
                timeout=self.docling_config.timeout_seconds
            )
            
            # Extract structured content
            structured_content = self._extract_structured_content(docling_result)
            
            # Extract metadata
            metadata = self._extract_metadata(docling_result, filename)
            
            # Extract tables
            tables = self._extract_tables(docling_result)
            
            # Extract images
            images = self._extract_images(docling_result)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score({
                "warnings": [],
                "errors": [],
                "content_length": len(structured_content.text) if structured_content else 0
            })
            
            return ProcessingResult(
                success=True,
                content=structured_content,
                metadata=metadata,
                tables=tables,
                images=images,
                processing_method=ProcessingMethod.DOCLING,
                processing_time=processing_time,
                confidence_score=confidence_score,
                warnings=[],
                errors=[],
                raw_data={"docling_result": docling_result}
            )
            
        except asyncio.TimeoutError:
            raise ProcessingTimeoutError(self.docling_config.timeout_seconds)
        except Exception as e:
            logger.error(f"Docling processing failed: {e}")
            
            # Return failed result
            processing_time = (datetime.now() - start_time).total_seconds()
            return ProcessingResult(
                success=False,
                processing_method=ProcessingMethod.DOCLING,
                processing_time=processing_time,
                confidence_score=0.0,
                errors=[str(e)]
            )
    
    async def _process_with_docling(
        self, 
        data_bytes: bytes, 
        input_format: Any,
        filename: Optional[str] = None
    ) -> DoclingDocument:
        """Process document with Docling in async context."""
        try:
            # Create temporary file for Docling processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{input_format.name.lower()}") as temp_file:
                temp_file.write(data_bytes)
                temp_file.flush()
                
                # Process with Docling
                result = self.converter.convert(temp_file.name)
                
                # Clean up temporary file
                os.unlink(temp_file.name)
                
                return result.document
                
        except Exception as e:
            raise ProcessingError(f"Docling processing failed: {str(e)}")
    
    def _get_input_format(self, file_type: DocumentType) -> Any:
        """Get Docling input format from document type."""
        format_mapping = {
            DocumentType.PDF: InputFormat.PDF,
            DocumentType.DOCX: InputFormat.DOCX,
            # Note: DOC format is not supported by Docling, only DOCX
        }
        
        if file_type not in format_mapping:
            raise UnsupportedFormatError(file_type.value, list(format_mapping.keys()))
        
        return format_mapping[file_type]
    
    def _extract_structured_content(self, docling_result: DoclingDocument) -> StructuredContent:
        """Extract structured content from Docling result."""
        try:
            # Get main text content
            text_content = docling_result.export_to_markdown()
            
            # Extract structural elements
            paragraphs = []
            headings = []
            lists = []
            footnotes = []
            citations = []
            formulas = []
            code_blocks = []
            reading_order = []
            
            # Process document elements
            for item in docling_result.body.main_text:
                element_data = {
                    "id": getattr(item, "id", None),
                    "text": getattr(item, "text", ""),
                    "type": item.__class__.__name__,
                    "position": getattr(item, "bbox", None)
                }
                
                # Categorize elements
                if "heading" in item.__class__.__name__.lower():
                    headings.append(element_data)
                elif "paragraph" in item.__class__.__name__.lower():
                    paragraphs.append(element_data)
                elif "list" in item.__class__.__name__.lower():
                    lists.append(element_data)
                
                # Add to reading order
                if element_data["id"]:
                    reading_order.append(element_data["id"])
            
            return StructuredContent(
                text=text_content,
                paragraphs=paragraphs,
                headings=headings,
                lists=lists,
                footnotes=footnotes,
                citations=citations,
                formulas=formulas,
                code_blocks=code_blocks,
                reading_order=reading_order
            )
            
        except Exception as e:
            raise ExtractionError("structured content", str(e))
    
    def _extract_metadata(
        self, 
        docling_result: DoclingDocument, 
        filename: Optional[str] = None
    ) -> DocumentMetadata:
        """Extract metadata from Docling result."""
        try:
            metadata = DocumentMetadata()
            
            # Extract basic metadata
            if hasattr(docling_result, "metadata") and docling_result.metadata:
                doc_meta = docling_result.metadata
                metadata.title = getattr(doc_meta, "title", None)
                metadata.author = getattr(doc_meta, "author", None)
                metadata.subject = getattr(doc_meta, "subject", None)
                metadata.creator = getattr(doc_meta, "creator", None)
                metadata.producer = getattr(doc_meta, "producer", None)
                
                # Handle dates
                if hasattr(doc_meta, "creation_date") and doc_meta.creation_date:
                    metadata.creation_date = doc_meta.creation_date
                if hasattr(doc_meta, "modification_date") and doc_meta.modification_date:
                    metadata.modification_date = doc_meta.modification_date
            
            # Count pages
            if hasattr(docling_result, "pages"):
                metadata.page_count = len(docling_result.pages)
            
            # Count words and characters
            text_content = docling_result.export_to_markdown()
            metadata.word_count = len(text_content.split())
            metadata.character_count = len(text_content)
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            return DocumentMetadata()
    
    def _extract_tables(self, docling_result: DoclingDocument) -> List[TableData]:
        """Extract tables from Docling result."""
        tables = []
        
        try:
            # Extract tables from document
            for i, table in enumerate(docling_result.tables):
                table_data = TableData(
                    table_id=f"table_{i}",
                    caption=getattr(table, "caption", None),
                    headers=[],
                    rows=[],
                    position=getattr(table, "bbox", {}),
                    confidence=1.0,
                    extraction_method="docling"
                )
                
                # Extract table content
                if hasattr(table, "data") and table.data:
                    # Convert table data to rows and headers
                    table_rows = table.data
                    if table_rows:
                        # First row as headers
                        table_data.headers = table_rows[0] if table_rows else []
                        # Remaining rows as data
                        table_data.rows = table_rows[1:] if len(table_rows) > 1 else []
                
                tables.append(table_data)
                
        except Exception as e:
            logger.warning(f"Failed to extract tables: {e}")
        
        return tables
    
    def _extract_images(self, docling_result: DoclingDocument) -> List[ImageData]:
        """Extract images from Docling result."""
        images = []
        
        try:
            # Extract images from document
            for i, figure in enumerate(docling_result.pictures):
                image_data = ImageData(
                    image_id=f"image_{i}",
                    caption=getattr(figure, "caption", None),
                    alt_text=getattr(figure, "alt_text", None),
                    image_data=getattr(figure, "image", None),
                    image_format=getattr(figure, "format", None),
                    position=getattr(figure, "bbox", {}),
                    confidence=1.0,
                    classification=getattr(figure, "classification", None)
                )
                
                # Extract dimensions if available
                if hasattr(figure, "width") and hasattr(figure, "height"):
                    image_data.dimensions = {
                        "width": figure.width,
                        "height": figure.height
                    }
                
                images.append(image_data)
                
        except Exception as e:
            logger.warning(f"Failed to extract images: {e}")
        
        return images
