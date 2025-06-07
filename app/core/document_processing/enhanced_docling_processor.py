#!/usr/bin/env python3
"""
Enhanced Docling Processor with Advanced Features

"""

import logging
import asyncio
import tempfile
import os
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime
from pathlib import Path

from app.core.document_processing.base import (
    DocumentProcessor, ProcessingResult, DocumentType,
    DocumentMetadata, TableData, ImageData, StructuredContent
)
from app.core.document_processing.exceptions import (
    ProcessingError, UnsupportedFormatError, ConfigurationError,
    ProcessingTimeoutError, ExtractionError
)
from app.core.document_processing.ocr.factory import OCREngineFactory, OCREngineConfiguration

logger = logging.getLogger(__name__)

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat, DocumentStream
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions, TableFormerMode, EasyOcrOptions
    )
    from docling.datamodel.document import DoclingDocument
    from docling.chunking import HybridChunker
    DOCLING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Docling not available: {e}")
    DOCLING_AVAILABLE = False
    DocumentConverter = None
    InputFormat = None
    PdfPipelineOptions = None
    DoclingDocument = None
    HybridChunker = None


class EnhancedDoclingConfiguration:
    """Enhanced configuration for Docling processor with advanced features."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        # Basic settings
        self.timeout_seconds = config.get("timeout_seconds", 300)
        self.max_file_size = config.get("max_file_size", 100 * 1024 * 1024)  # 100MB
        self.max_pages = config.get("max_pages", 1000)
        
        # Advanced PDF processing options
        self.enable_ocr = config.get("enable_ocr", True)
        self.enable_table_structure = config.get("enable_table_structure", True)
        self.enable_picture_extraction = config.get("enable_picture_extraction", True)
        self.enable_formula_detection = config.get("enable_formula_detection", True)
        self.enable_code_detection = config.get("enable_code_detection", True)
        
        # Table processing options
        self.table_mode = config.get("table_mode", "accurate")  # "fast" or "accurate"
        self.enable_cell_matching = config.get("enable_cell_matching", True)
        
        # OCR options (legacy - for backward compatibility)
        self.ocr_language = config.get("ocr_language", ["en"])
        self.ocr_engine = config.get("ocr_engine", "rapidocr")  # "easyocr", "tesseract", "rapidocr", "mistral"

        # Enhanced OCR configuration
        self.enhanced_ocr_config = OCREngineConfiguration({
            "primary_ocr_engine": config.get("primary_ocr_engine", "rapidocr"),
            "fallback_ocr_engines": config.get("fallback_ocr_engines", ["easyocr", "tesseract"]),
            "enable_ocr_fallback": config.get("enable_ocr_fallback", True),
            "ocr_quality_threshold": config.get("ocr_quality_threshold", 0.7),
            "cost_optimization": config.get("cost_optimization", False),
            "local_ocr_priority": config.get("local_ocr_priority", True),
            "budget_per_document": config.get("budget_per_document", 1.0),
            "mistral_api_key": config.get("mistral_api_key"),
            "mistral_model": config.get("mistral_model", "mistral-ocr-latest"),
            "easyocr_languages": self.ocr_language,
            "max_concurrent_requests": config.get("max_concurrent_requests", 5)
        })
        
        # Remote services (disabled by default for security)
        self.enable_remote_services = config.get("enable_remote_services", False)
        
        # Chunking options
        self.enable_chunking = config.get("enable_chunking", True)
        self.chunk_tokenizer = config.get("chunk_tokenizer", "BAAI/bge-small-en-v1.5")
        self.chunk_max_tokens = config.get("chunk_max_tokens", 512)
        
        # VLM options
        self.enable_vlm = config.get("enable_vlm", False)
        self.vlm_model = config.get("vlm_model", "smoldocling")
        
        # Performance options
        self.cpu_threads = config.get("cpu_threads", 4)
        self.artifacts_path = config.get("artifacts_path", None)
        
    @property
    def pdf_options(self) -> Any:
        """Get PDF pipeline options."""
        if not DOCLING_AVAILABLE:
            return None
            
        options = PdfPipelineOptions(
            artifacts_path=self.artifacts_path,
            do_ocr=self.enable_ocr,
            do_table_structure=self.enable_table_structure,
            do_picture_extraction=self.enable_picture_extraction,
            enable_remote_services=self.enable_remote_services
        )
        
        # Configure table structure options
        if self.enable_table_structure:
            options.table_structure_options.do_cell_matching = self.enable_cell_matching
            if self.table_mode == "fast":
                options.table_structure_options.mode = TableFormerMode.FAST
            else:
                options.table_structure_options.mode = TableFormerMode.ACCURATE
        
        # Configure OCR options
        if self.enable_ocr:
            options.ocr_options = EasyOcrOptions(
                lang=self.ocr_language,
                force_full_page_ocr=False
            )
        
        return options


class EnhancedDoclingProcessor(DocumentProcessor):
    """Enhanced Docling processor with advanced document processing capabilities."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize enhanced Docling processor."""
        super().__init__(config)
        
        if not DOCLING_AVAILABLE:
            raise ConfigurationError("Docling is not available. Please install docling>=2.36.0")
        
        self.docling_config = EnhancedDoclingConfiguration(config)
        self.converter = self._create_converter()
        self.chunker = self._create_chunker() if self.docling_config.enable_chunking else None

        # Initialize OCR engine factory for enhanced document processing
        self.ocr_factory = OCREngineFactory(self.docling_config.enhanced_ocr_config)
        self.ocr_engines = None  # Will be initialized on first use
        
        # Set CPU threads for performance
        if self.docling_config.cpu_threads:
            os.environ["OMP_NUM_THREADS"] = str(self.docling_config.cpu_threads)
    
    def _create_converter(self) -> DocumentConverter:
        """Create and configure enhanced Docling document converter."""
        try:
            format_options = {}
            
            # Add PDF options with advanced features
            if self.docling_config.pdf_options:
                format_options[InputFormat.PDF] = self.docling_config.pdf_options
            
            # Add Word document options
            format_options[InputFormat.DOCX] = {}
            
            # Add other format options
            format_options[InputFormat.HTML] = {}
            format_options[InputFormat.XLSX] = {}
            
            return DocumentConverter(format_options=format_options)
            
        except Exception as e:
            raise ConfigurationError(f"Failed to create enhanced Docling converter: {str(e)}")
    
    def _create_chunker(self) -> Optional[Any]:
        """Create document chunker for advanced text processing."""
        try:
            if not DOCLING_AVAILABLE or not HybridChunker:
                return None
                
            return HybridChunker(
                tokenizer=self.docling_config.chunk_tokenizer,
                max_tokens=self.docling_config.chunk_max_tokens
            )
        except Exception as e:
            logger.warning(f"Failed to create chunker: {e}")
            return None
    
    def supports_format(self, file_type: DocumentType) -> bool:
        """Check if processor supports the given format."""
        supported = {
            DocumentType.PDF,
            DocumentType.DOCX,
            DocumentType.HTML,
            DocumentType.TXT,  # Enhanced support
            DocumentType.RTF,  # Enhanced support
            DocumentType.ODT,  # Enhanced support
            DocumentType.IMAGE,  # Enhanced OCR support
        }
        return file_type in supported

    def get_supported_formats(self) -> List[DocumentType]:
        """Get list of supported document formats."""
        return [
            DocumentType.PDF,
            DocumentType.DOCX,
            DocumentType.HTML,
            DocumentType.TXT,
            DocumentType.RTF,
            DocumentType.ODT,
            DocumentType.IMAGE,  # Enhanced OCR support
        ]
    
    async def process_document(
        self, 
        file_data: Union[bytes, BinaryIO], 
        file_type: DocumentType,
        filename: Optional[str] = None,
        **kwargs
    ) -> ProcessingResult:
        """
        Process document using enhanced Docling capabilities.
        
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
            self.validate_input(file_data, file_type, self.docling_config.max_file_size)
            
            # Convert file data to bytes if needed
            if isinstance(file_data, bytes):
                data_bytes = file_data
            else:
                data_bytes = file_data.read()
            
            # Check if this is an image document that needs OCR processing
            if file_type == DocumentType.IMAGE:
                docling_result = await self._process_image_with_ocr(data_bytes, filename)
            else:
                # Get input format for Docling
                input_format = self._get_input_format(file_type)

                # If no input format (text files), use text processing
                if input_format is None:
                    docling_result = await self._process_as_text(data_bytes, filename)
                else:
                    # Process document with timeout
                    docling_result = await asyncio.wait_for(
                        self._process_with_enhanced_docling(data_bytes, input_format, filename),
                        timeout=self.docling_config.timeout_seconds
                    )
            
            # Extract structured content with advanced features
            structured_content = self._extract_enhanced_structured_content(docling_result)
            
            # Extract metadata with advanced features
            metadata = self._extract_enhanced_metadata(docling_result, filename)
            
            # Extract tables with advanced structure recognition
            tables = self._extract_enhanced_tables(docling_result)
            
            # Extract images with classification
            images = self._extract_enhanced_images(docling_result)
            
            # Perform chunking if enabled
            chunks = self._extract_chunks(docling_result) if self.chunker else []
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessingResult(
                success=True,
                content=structured_content,
                metadata=metadata,
                tables=tables,
                images=images,
                processing_time=processing_time,
                raw_data={
                    "chunks": chunks,
                    "docling_version": "2.36.0+",
                    "processor_name": "enhanced_docling",
                    "advanced_features_used": {
                        "ocr": self.docling_config.enable_ocr,
                        "table_structure": self.docling_config.enable_table_structure,
                        "picture_extraction": self.docling_config.enable_picture_extraction,
                        "formula_detection": self.docling_config.enable_formula_detection,
                        "chunking": self.docling_config.enable_chunking
                    }
                }
            )
            
        except asyncio.TimeoutError:
            raise ProcessingTimeoutError(
                f"Document processing timed out after {self.docling_config.timeout_seconds} seconds"
            )
        except Exception as e:
            logger.error(f"Enhanced Docling processing failed: {str(e)}")
            raise ProcessingError(f"Enhanced Docling processing failed: {str(e)}")
    
    async def _process_with_enhanced_docling(
        self, 
        data_bytes: bytes, 
        input_format: Any,
        filename: Optional[str] = None
    ) -> DoclingDocument:
        """Process document with enhanced Docling features."""
        try:
            from io import BytesIO

            # Create document stream for processing
            if filename and input_format:
                # Create BytesIO stream for DocumentStream
                stream = BytesIO(data_bytes)
                source = DocumentStream(name=filename, stream=stream)
            else:
                # Create temporary file for processing
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".txt" if not input_format else f".{input_format.name.lower()}"
                ) as temp_file:
                    temp_file.write(data_bytes)
                    temp_file.flush()
                    source = temp_file.name
            
            # Process with enhanced Docling converter
            result = self.converter.convert(
                source,
                max_num_pages=self.docling_config.max_pages,
                max_file_size=self.docling_config.max_file_size
            )
            
            # Clean up temporary file if created
            if isinstance(source, str) and os.path.exists(source):
                os.unlink(source)
            
            return result.document
            
        except Exception as e:
            raise ProcessingError(f"Enhanced Docling processing failed: {str(e)}")

    async def _process_image_with_ocr(self, data_bytes: bytes, filename: Optional[str]) -> Any:
        """Process image document using OCR engines."""
        try:
            # Initialize OCR engines if not already done
            if self.ocr_engines is None:
                self.ocr_engines = await self.ocr_factory.initialize_engines()

            # Process image with OCR using fallback mechanism
            ocr_result = await self.ocr_factory.process_with_fallback(
                data_bytes,
                "image",
                language=self.docling_config.ocr_language[0] if self.docling_config.ocr_language else "en"
            )

            # Create a mock document object compatible with Docling structure
            class MockOCRDocument:
                def __init__(self, ocr_result, filename):
                    self.ocr_result = ocr_result
                    self.filename = filename
                    self.text = ocr_result.text
                    self.texts = [MockTextItem(ocr_result.text, "text", 1)]
                    self.tables = []
                    self.pictures = [MockImageItem(filename or "image", data_bytes)]

                def export_to_markdown(self):
                    return self.text

            class MockTextItem:
                def __init__(self, text, label, page_no):
                    self.text = text
                    self.label = label
                    self.page_no = page_no
                    self.bbox = None

            class MockImageItem:
                def __init__(self, name, data):
                    self.name = name
                    self.data = data
                    self.page_no = 1

            return MockOCRDocument(ocr_result, filename)

        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise ProcessingError(f"OCR processing failed: {str(e)}")

    async def _process_as_text(self, data_bytes: bytes, filename: Optional[str]) -> Any:
        """Process document as plain text when Docling format is not supported."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
            text_content = None

            for encoding in encodings:
                try:
                    text_content = data_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if text_content is None:
                text_content = data_bytes.decode('utf-8', errors='ignore')

            # Create a mock document object for compatibility
            class MockTextDocument:
                def __init__(self, text):
                    self.text = text
                    self.texts = [MockTextItem(text, "text")]
                    self.tables = []
                    self.pictures = []

                def export_to_markdown(self):
                    return self.text

            class MockTextItem:
                def __init__(self, text, label):
                    self.text = text
                    self.label = label
                    self.page_no = 1

            return MockTextDocument(text_content)

        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            raise ProcessingError(f"Text processing failed: {str(e)}")

    def _get_input_format(self, file_type: DocumentType) -> Any:
        """Get Docling input format from document type."""
        if not DOCLING_AVAILABLE or not InputFormat:
            raise ConfigurationError("Docling not available")

        format_mapping = {
            DocumentType.PDF: InputFormat.PDF,
            DocumentType.DOCX: InputFormat.DOCX,
            DocumentType.HTML: InputFormat.HTML,
            # Note: TXT, RTF, ODT may need special handling or conversion
        }

        if file_type not in format_mapping:
            # For unsupported formats, try to handle as text
            if file_type in [DocumentType.TXT, DocumentType.RTF, DocumentType.ODT]:
                # These will be handled as text files - return None to use text processing
                logger.info(f"Using text processing for {file_type.value} format")
                return None
            else:
                logger.warning(f"Unsupported format {file_type.value}, attempting text processing")
                return None  # Try text processing instead of raising error

        return format_mapping[file_type]

    def _extract_enhanced_structured_content(self, doc: Any) -> StructuredContent:
        """Extract structured content with enhanced features."""
        try:
            # Get main text content
            main_text = doc.export_to_markdown()

            # Extract headings with hierarchy
            headings = []
            for item in doc.texts:
                if hasattr(item, 'label') and 'heading' in item.label.lower():
                    headings.append({
                        'text': item.text,
                        'level': self._extract_heading_level(item.label),
                        'page': getattr(item, 'page_no', None)
                    })

            # Extract paragraphs with enhanced metadata
            paragraphs = []
            for item in doc.texts:
                if hasattr(item, 'label') and item.label.lower() in ['text', 'paragraph']:
                    paragraphs.append({
                        'text': item.text,
                        'page': getattr(item, 'page_no', None),
                        'bbox': getattr(item, 'bbox', None)
                    })

            # Extract lists
            lists = []
            for item in doc.texts:
                if hasattr(item, 'label') and 'list' in item.label.lower():
                    lists.append({
                        'text': item.text,
                        'type': item.label,
                        'page': getattr(item, 'page_no', None)
                    })

            # Extract code blocks
            code_blocks = []
            for item in doc.texts:
                if hasattr(item, 'label') and 'code' in item.label.lower():
                    code_blocks.append({
                        'text': item.text,
                        'language': self._detect_code_language(item.text),
                        'page': getattr(item, 'page_no', None)
                    })

            # Extract formulas
            formulas = []
            for item in doc.texts:
                if hasattr(item, 'label') and 'formula' in item.label.lower():
                    formulas.append({
                        'text': item.text,
                        'type': 'mathematical',
                        'page': getattr(item, 'page_no', None)
                    })

            return StructuredContent(
                text=main_text,
                headings=headings,
                paragraphs=paragraphs,
                lists=lists,
                code_blocks=code_blocks,
                formulas=formulas
            )

        except Exception as e:
            logger.error(f"Enhanced content extraction failed: {e}")
            # Fallback to basic text extraction
            return StructuredContent(
                text=doc.export_to_markdown() if doc else "",
                headings=[],
                paragraphs=[],
                lists=[]
            )

    def _extract_enhanced_metadata(self, doc: Any, filename: Optional[str] = None) -> DocumentMetadata:
        """Extract enhanced metadata from document."""
        try:
            # Basic metadata
            page_count = len(set(getattr(item, 'page_no', 0) for item in doc.texts))
            word_count = len(doc.export_to_markdown().split())

            # Enhanced metadata extraction
            languages = self._detect_languages(doc)
            document_type = self._classify_document_type(doc)

            # Extract structural information
            structure_info = {
                'has_tables': len(getattr(doc, 'tables', [])) > 0,
                'has_images': len(getattr(doc, 'pictures', [])) > 0,
                'has_formulas': any('formula' in getattr(item, 'label', '').lower() for item in doc.texts),
                'has_code': any('code' in getattr(item, 'label', '').lower() for item in doc.texts),
                'heading_count': len([item for item in doc.texts if 'heading' in getattr(item, 'label', '').lower()]),
                'table_count': len(getattr(doc, 'tables', [])),
                'image_count': len(getattr(doc, 'pictures', []))
            }

            return DocumentMetadata(
                title=self._extract_title(doc),
                author=self._extract_author(doc),
                creation_date=None,  # Docling doesn't extract this by default
                modification_date=None,
                page_count=page_count,
                word_count=word_count,
                language=languages[0] if languages else "unknown",
                file_size=None,  # Not available from Docling
                custom_properties={
                    'filename': filename,
                    'languages_detected': languages,
                    'document_type': document_type,
                    'structure_info': structure_info,
                    'processing_method': 'enhanced_docling'
                }
            )

        except Exception as e:
            logger.error(f"Enhanced metadata extraction failed: {e}")
            return DocumentMetadata(
                title=filename or "Unknown",
                author="Unknown",
                creation_date=None,
                modification_date=None,
                page_count=0,
                word_count=0,
                language="unknown",
                file_size=None,
                custom_properties={'extraction_error': str(e)}
            )

    def _extract_enhanced_tables(self, doc: Any) -> List[TableData]:
        """Extract tables with enhanced structure recognition."""
        tables = []

        try:
            if not hasattr(doc, 'tables') or not doc.tables:
                return tables

            for i, table in enumerate(doc.tables):
                try:
                    # Extract table data with enhanced structure
                    table_data = self._process_enhanced_table(table, i)
                    if table_data:
                        tables.append(table_data)

                except Exception as e:
                    logger.warning(f"Failed to process table {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Enhanced table extraction failed: {e}")

        return tables

    def _extract_enhanced_images(self, doc: Any) -> List[ImageData]:
        """Extract images with classification and metadata."""
        images = []

        try:
            if not hasattr(doc, 'pictures') or not doc.pictures:
                return images

            for i, picture in enumerate(doc.pictures):
                try:
                    # Extract image with enhanced metadata
                    image_data = self._process_enhanced_image(picture, i)
                    if image_data:
                        images.append(image_data)

                except Exception as e:
                    logger.warning(f"Failed to process image {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Enhanced image extraction failed: {e}")

        return images

    def _extract_chunks(self, doc: Any) -> List[Dict[str, Any]]:
        """Extract document chunks for RAG applications."""
        chunks = []

        try:
            if not self.chunker:
                return chunks

            # Generate chunks using HybridChunker
            chunk_iter = self.chunker.chunk(doc)

            for i, chunk in enumerate(chunk_iter):
                chunks.append({
                    'id': i,
                    'text': chunk.get('text', ''),
                    'metadata': chunk.get('meta', {}),
                    'token_count': len(chunk.get('text', '').split()),
                    'page_references': self._extract_page_references(chunk)
                })

        except Exception as e:
            logger.error(f"Document chunking failed: {e}")

        return chunks

    # Helper methods for enhanced processing
    def _extract_heading_level(self, label: str) -> int:
        """Extract heading level from label."""
        try:
            if 'h1' in label.lower() or 'heading-1' in label.lower():
                return 1
            elif 'h2' in label.lower() or 'heading-2' in label.lower():
                return 2
            elif 'h3' in label.lower() or 'heading-3' in label.lower():
                return 3
            elif 'h4' in label.lower() or 'heading-4' in label.lower():
                return 4
            elif 'h5' in label.lower() or 'heading-5' in label.lower():
                return 5
            elif 'h6' in label.lower() or 'heading-6' in label.lower():
                return 6
            else:
                return 1  # Default to h1
        except:
            return 1

    def _detect_code_language(self, code_text: str) -> str:
        """Detect programming language from code text."""
        code_lower = code_text.lower()

        # Simple language detection based on keywords
        if any(keyword in code_lower for keyword in ['def ', 'import ', 'from ', 'class ']):
            return 'python'
        elif any(keyword in code_lower for keyword in ['function', 'var ', 'let ', 'const ']):
            return 'javascript'
        elif any(keyword in code_lower for keyword in ['public class', 'private ', 'public static']):
            return 'java'
        elif any(keyword in code_lower for keyword in ['#include', 'int main', 'printf']):
            return 'c'
        elif any(keyword in code_lower for keyword in ['SELECT', 'FROM', 'WHERE', 'INSERT']):
            return 'sql'
        else:
            return 'unknown'

    def _detect_languages(self, doc: Any) -> List[str]:
        """Detect languages in document."""
        # Simple language detection - could be enhanced with proper language detection
        text = doc.export_to_markdown() if doc else ""

        # Basic language detection based on common words
        if any(word in text.lower() for word in ['the', 'and', 'or', 'but', 'in', 'on', 'at']):
            return ['en']
        elif any(word in text.lower() for word in ['le', 'la', 'et', 'ou', 'dans', 'sur']):
            return ['fr']
        elif any(word in text.lower() for word in ['der', 'die', 'das', 'und', 'oder', 'in', 'auf']):
            return ['de']
        else:
            return ['unknown']

    def _classify_document_type(self, doc: Any) -> str:
        """Classify document type based on content."""
        try:
            text = doc.export_to_markdown() if doc else ""
            text_lower = text.lower()

            # Check for academic paper indicators
            if any(term in text_lower for term in ['abstract', 'introduction', 'methodology', 'conclusion', 'references']):
                return 'academic_paper'

            # Check for report indicators
            elif any(term in text_lower for term in ['executive summary', 'findings', 'recommendations']):
                return 'report'

            # Check for legal document indicators
            elif any(term in text_lower for term in ['whereas', 'hereby', 'agreement', 'contract']):
                return 'legal_document'

            # Check for technical documentation
            elif any(term in text_lower for term in ['api', 'documentation', 'installation', 'configuration']):
                return 'technical_documentation'

            else:
                return 'general_document'

        except:
            return 'unknown'

    def _extract_title(self, doc: Any) -> str:
        """Extract document title."""
        try:
            # Look for title in headings
            for item in doc.texts:
                if hasattr(item, 'label') and 'title' in item.label.lower():
                    return item.text.strip()
                elif hasattr(item, 'label') and 'h1' in item.label.lower():
                    return item.text.strip()

            # Fallback to first heading
            for item in doc.texts:
                if hasattr(item, 'label') and 'heading' in item.label.lower():
                    return item.text.strip()

            return "Untitled Document"

        except:
            return "Untitled Document"

    def _extract_author(self, doc: Any) -> str:
        """Extract document author."""
        try:
            # Look for author information in metadata or text
            text = doc.export_to_markdown() if doc else ""

            # Simple author extraction patterns
            import re
            author_patterns = [
                r'author[s]?:\s*([^\n]+)',
                r'by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'written\s+by\s+([^\n]+)'
            ]

            for pattern in author_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

            return "Unknown Author"

        except:
            return "Unknown Author"

    def _process_enhanced_table(self, table: Any, index: int) -> Optional[TableData]:
        """Process table with enhanced structure recognition."""
        try:
            # Extract table data with structure information
            rows = []
            headers = []

            # Get table structure if available
            if hasattr(table, 'data') and table.data:
                table_data = table.data

                # Extract headers (first row)
                if table_data and len(table_data) > 0:
                    headers = [str(cell) for cell in table_data[0]]

                    # Extract data rows
                    for row_data in table_data[1:]:
                        row = [str(cell) for cell in row_data]
                        rows.append(row)

            # Get table metadata
            caption = getattr(table, 'caption', f"Table {index + 1}")
            page_number = getattr(table, 'page_no', None)
            bbox = getattr(table, 'bbox', None)

            return TableData(
                table_id=f"table_{index}",
                headers=headers,
                rows=rows,
                caption=caption,
                position={
                    'table_index': index,
                    'page_number': page_number,
                    'bbox': bbox
                },
                extraction_method='enhanced_docling'
            )

        except Exception as e:
            logger.warning(f"Failed to process enhanced table {index}: {e}")
            return None

    def _process_enhanced_image(self, picture: Any, index: int) -> Optional[ImageData]:
        """Process image with classification and metadata."""
        try:
            # Extract image metadata
            caption = getattr(picture, 'caption', f"Image {index + 1}")
            page_number = getattr(picture, 'page_no', None)
            bbox = getattr(picture, 'bbox', None)

            # Classify image type based on available information
            image_type = self._classify_image_type(picture)

            return ImageData(
                image_id=f"image_{index}",
                caption=caption,
                alt_text=caption,  # Use caption as alt text
                position={
                    'image_index': index,
                    'page_number': page_number,
                    'bbox': bbox
                },
                classification=image_type
            )

        except Exception as e:
            logger.warning(f"Failed to process enhanced image {index}: {e}")
            return None

    def _classify_image_type(self, picture: Any) -> str:
        """Classify image type."""
        try:
            # Check if classification is available from Docling
            if hasattr(picture, 'classification'):
                return picture.classification

            # Fallback classification based on caption or context
            caption = getattr(picture, 'caption', '').lower()

            if any(term in caption for term in ['chart', 'graph', 'plot']):
                return 'chart'
            elif any(term in caption for term in ['diagram', 'flowchart', 'schema']):
                return 'diagram'
            elif any(term in caption for term in ['photo', 'image', 'picture']):
                return 'photograph'
            elif any(term in caption for term in ['table', 'matrix']):
                return 'table_image'
            else:
                return 'unknown'

        except:
            return 'unknown'

    def _extract_page_references(self, chunk: Dict[str, Any]) -> List[int]:
        """Extract page references from chunk metadata."""
        try:
            pages = set()
            meta = chunk.get('meta', {})

            # Extract page numbers from doc_items
            doc_items = meta.get('doc_items', [])
            for item in doc_items:
                prov = item.get('prov', [])
                for p in prov:
                    page_no = p.get('page_no')
                    if page_no is not None:
                        pages.add(page_no)

            return sorted(list(pages))

        except:
            return []
