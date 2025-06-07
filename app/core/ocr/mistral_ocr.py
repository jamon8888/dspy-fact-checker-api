"""
Mistral OCR integration for advanced optical character recognition.
"""

import logging
import asyncio
import base64
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime
import tempfile
import os
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)

try:
    from mistralai import Mistral
    from mistralai.models import DocumentURLChunk, ImageURLChunk
    MISTRAL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Mistral AI not available: {e}")
    MISTRAL_AVAILABLE = False
    Mistral = None
    DocumentURLChunk = None
    ImageURLChunk = None


class MistralOCRError(Exception):
    """Base exception for Mistral OCR errors."""
    pass


class MistralOCRConfigurationError(MistralOCRError):
    """Configuration error for Mistral OCR."""
    pass


class MistralOCRProcessingError(MistralOCRError):
    """Processing error for Mistral OCR."""
    pass


class MistralOCRRateLimitError(MistralOCRError):
    """Rate limit error for Mistral OCR."""
    pass


class MistralOCRProcessor:
    """
    Advanced OCR processor using Mistral AI's OCR API.
    
    Features:
    - High-accuracy text extraction from images and PDFs
    - Multi-language support
    - Complex layout understanding
    - Table and structure preservation
    - Image classification and metadata extraction
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Mistral OCR processor."""
        if not MISTRAL_AVAILABLE:
            raise MistralOCRConfigurationError(
                "Mistral AI is not available. Please install mistralai>=1.0.0"
            )
        
        self.settings = get_settings()
        self.api_key = api_key or self.settings.MISTRAL_API_KEY
        
        if not self.api_key:
            raise MistralOCRConfigurationError(
                "Mistral API key is required. Set MISTRAL_API_KEY environment variable."
            )
        
        self.client = Mistral(api_key=self.api_key)
        self.model = "mistral-ocr-latest"
        
        # Configuration
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit from Mistral
        self.max_pages = 1000  # 1000 pages limit from Mistral
        self.timeout_seconds = 300  # 5 minutes timeout
        
        logger.info("Mistral OCR processor initialized successfully")
    
    async def process_image(
        self,
        image_data: Union[bytes, str],
        image_format: str = "jpeg",
        include_image_base64: bool = False,
        bbox_annotation_format: Optional[Dict[str, Any]] = None,
        document_annotation_format: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process an image using Mistral OCR.
        
        Args:
            image_data: Image data as bytes or base64 string
            image_format: Image format (jpeg, png, etc.)
            include_image_base64: Whether to include image base64 in response
            **kwargs: Additional processing options
            
        Returns:
            OCR results with extracted text and metadata
        """
        try:
            # Prepare image data
            if isinstance(image_data, bytes):
                base64_image = base64.b64encode(image_data).decode('utf-8')
            else:
                base64_image = image_data
            
            # Validate file size
            estimated_size = len(base64_image) * 3 / 4  # Rough base64 to bytes conversion
            if estimated_size > self.max_file_size:
                raise MistralOCRProcessingError(
                    f"Image size ({estimated_size:.1f}MB) exceeds maximum allowed size (50MB)"
                )
            
            # Prepare image URL
            image_url = f"data:image/{image_format};base64,{base64_image}"
            
            # Process with Mistral OCR
            start_time = datetime.now()
            
            ocr_response = await asyncio.wait_for(
                self._process_with_mistral_ocr(
                    document_type="image_url",
                    document_url=image_url,
                    include_image_base64=include_image_base64,
                    bbox_annotation_format=bbox_annotation_format,
                    document_annotation_format=document_annotation_format
                ),
                timeout=self.timeout_seconds
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Structure the response
            result = {
                "success": True,
                "text": ocr_response.get("text", ""),
                "markdown": ocr_response.get("markdown", ""),
                "metadata": {
                    "model": self.model,
                    "processing_time": processing_time,
                    "image_format": image_format,
                    "confidence_score": self._calculate_confidence_score(ocr_response),
                    "language": self._detect_language(ocr_response.get("text", "")),
                    "character_count": len(ocr_response.get("text", "")),
                    "word_count": len(ocr_response.get("text", "").split()),
                    "usage": ocr_response.get("usage", {})
                },
                "images": ocr_response.get("images", []),
                "bbox_annotations": ocr_response.get("bbox_annotations", []),
                "document_annotation": ocr_response.get("document_annotation", {}),
                "tables": self._extract_tables_from_markdown(ocr_response.get("markdown", "")),
                "structure": self._analyze_document_structure(ocr_response.get("markdown", "")),
                "raw_response": ocr_response if kwargs.get("include_raw", False) else None
            }
            
            logger.info(f"Image OCR completed successfully in {processing_time:.2f}s")
            return result
            
        except asyncio.TimeoutError:
            raise MistralOCRProcessingError(f"OCR processing timed out after {self.timeout_seconds}s")
        except Exception as e:
            logger.error(f"Image OCR processing failed: {e}")
            raise MistralOCRProcessingError(f"Failed to process image: {str(e)}")
    
    async def process_pdf(
        self,
        pdf_data: Union[bytes, str],
        include_image_base64: bool = False,
        pages: Optional[List[int]] = None,
        bbox_annotation_format: Optional[Dict[str, Any]] = None,
        document_annotation_format: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a PDF document using Mistral OCR.
        
        Args:
            pdf_data: PDF data as bytes or base64 string
            include_image_base64: Whether to include image base64 in response
            **kwargs: Additional processing options
            
        Returns:
            OCR results with extracted text and metadata
        """
        try:
            # Prepare PDF data
            if isinstance(pdf_data, bytes):
                base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
            else:
                base64_pdf = pdf_data
            
            # Validate file size
            estimated_size = len(base64_pdf) * 3 / 4  # Rough base64 to bytes conversion
            if estimated_size > self.max_file_size:
                raise MistralOCRProcessingError(
                    f"PDF size ({estimated_size:.1f}MB) exceeds maximum allowed size (50MB)"
                )
            
            # Prepare document URL
            document_url = f"data:application/pdf;base64,{base64_pdf}"
            
            # Process with Mistral OCR
            start_time = datetime.now()
            
            ocr_response = await asyncio.wait_for(
                self._process_with_mistral_ocr(
                    document_type="document_url",
                    document_url=document_url,
                    include_image_base64=include_image_base64,
                    pages=pages,
                    bbox_annotation_format=bbox_annotation_format,
                    document_annotation_format=document_annotation_format
                ),
                timeout=self.timeout_seconds
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Structure the response
            result = {
                "success": True,
                "text": ocr_response.get("text", ""),
                "markdown": ocr_response.get("markdown", ""),
                "metadata": {
                    "model": self.model,
                    "processing_time": processing_time,
                    "document_type": "pdf",
                    "confidence_score": self._calculate_confidence_score(ocr_response),
                    "language": self._detect_language(ocr_response.get("text", "")),
                    "character_count": len(ocr_response.get("text", "")),
                    "word_count": len(ocr_response.get("text", "").split()),
                    "estimated_pages": self._estimate_page_count(ocr_response.get("text", "")),
                    "pages_processed": pages,
                    "usage": ocr_response.get("usage", {})
                },
                "images": ocr_response.get("images", []),
                "bbox_annotations": ocr_response.get("bbox_annotations", []),
                "document_annotation": ocr_response.get("document_annotation", {}),
                "tables": self._extract_tables_from_markdown(ocr_response.get("markdown", "")),
                "structure": self._analyze_document_structure(ocr_response.get("markdown", "")),
                "raw_response": ocr_response if kwargs.get("include_raw", False) else None
            }
            
            logger.info(f"PDF OCR completed successfully in {processing_time:.2f}s")
            return result
            
        except asyncio.TimeoutError:
            raise MistralOCRProcessingError(f"OCR processing timed out after {self.timeout_seconds}s")
        except Exception as e:
            logger.error(f"PDF OCR processing failed: {e}")
            raise MistralOCRProcessingError(f"Failed to process PDF: {str(e)}")
    
    async def process_url(
        self, 
        document_url: str, 
        include_image_base64: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a document from URL using Mistral OCR.
        
        Args:
            document_url: URL of the document to process
            include_image_base64: Whether to include image base64 in response
            **kwargs: Additional processing options
            
        Returns:
            OCR results with extracted text and metadata
        """
        try:
            # Determine document type from URL
            document_type = self._determine_document_type_from_url(document_url)
            
            # Process with Mistral OCR
            start_time = datetime.now()
            
            ocr_response = await asyncio.wait_for(
                self._process_with_mistral_ocr(
                    document_type=document_type,
                    document_url=document_url,
                    include_image_base64=include_image_base64
                ),
                timeout=self.timeout_seconds
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Structure the response
            result = {
                "success": True,
                "text": ocr_response.get("text", ""),
                "markdown": ocr_response.get("markdown", ""),
                "metadata": {
                    "model": self.model,
                    "processing_time": processing_time,
                    "source_url": document_url,
                    "document_type": document_type,
                    "confidence_score": self._calculate_confidence_score(ocr_response),
                    "language": self._detect_language(ocr_response.get("text", "")),
                    "character_count": len(ocr_response.get("text", "")),
                    "word_count": len(ocr_response.get("text", "").split())
                },
                "images": ocr_response.get("images", []),
                "tables": self._extract_tables_from_markdown(ocr_response.get("markdown", "")),
                "structure": self._analyze_document_structure(ocr_response.get("markdown", "")),
                "raw_response": ocr_response if kwargs.get("include_raw", False) else None
            }
            
            logger.info(f"URL OCR completed successfully in {processing_time:.2f}s")
            return result
            
        except asyncio.TimeoutError:
            raise MistralOCRProcessingError(f"OCR processing timed out after {self.timeout_seconds}s")
        except Exception as e:
            logger.error(f"URL OCR processing failed: {e}")
            raise MistralOCRProcessingError(f"Failed to process URL: {str(e)}")
    
    async def _process_with_mistral_ocr(
        self,
        document_type: str,
        document_url: str,
        include_image_base64: bool = False,
        pages: Optional[List[int]] = None,
        bbox_annotation_format: Optional[Dict[str, Any]] = None,
        document_annotation_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process document with Mistral OCR API using official API structure."""
        try:
            # Prepare document chunk based on type
            if document_type == "image_url":
                if ImageURLChunk:
                    document_chunk = ImageURLChunk(image_url=document_url)
                else:
                    # Fallback for when mistralai is not available
                    document_chunk = {"type": "image_url", "image_url": document_url}
            else:
                if DocumentURLChunk:
                    document_chunk = DocumentURLChunk(document_url=document_url)
                else:
                    # Fallback for when mistralai is not available
                    document_chunk = {"type": "document_url", "document_url": document_url}

            # Prepare request parameters
            request_params = {
                "model": self.model,
                "document": document_chunk,
                "include_image_base64": include_image_base64
            }

            # Add optional parameters
            if pages is not None:
                request_params["pages"] = pages

            if bbox_annotation_format:
                request_params["bbox_annotation_format"] = bbox_annotation_format

            if document_annotation_format:
                request_params["document_annotation_format"] = document_annotation_format

            # Make the API call
            response = await asyncio.to_thread(
                self.client.ocr.process,
                **request_params
            )

            # Extract response data according to official API response structure
            result = {
                "text": getattr(response, "text", ""),
                "markdown": getattr(response, "markdown", ""),
                "images": getattr(response, "images", []),
                "bbox_annotations": getattr(response, "bbox_annotations", []),
                "document_annotation": getattr(response, "document_annotation", {}),
                "metadata": getattr(response, "metadata", {}),
                "usage": getattr(response, "usage", {})
            }

            return result

        except Exception as e:
            # Handle specific Mistral API errors
            error_message = str(e).lower()
            if "rate limit" in error_message or "quota" in error_message:
                raise MistralOCRRateLimitError(f"Rate limit exceeded: {str(e)}")
            elif "unauthorized" in error_message or "api key" in error_message:
                raise MistralOCRConfigurationError(f"Authentication failed: {str(e)}")
            else:
                raise MistralOCRProcessingError(f"Mistral OCR API error: {str(e)}")
    
    def _determine_document_type_from_url(self, url: str) -> str:
        """Determine document type from URL."""
        url_lower = url.lower()
        
        # Check for image formats
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.avif']
        if any(ext in url_lower for ext in image_extensions):
            return "image_url"
        
        # Check for document formats
        document_extensions = ['.pdf', '.docx', '.pptx', '.doc', '.ppt']
        if any(ext in url_lower for ext in document_extensions):
            return "document_url"
        
        # Default to document_url for unknown types
        return "document_url"
    
    def _calculate_confidence_score(self, ocr_response: Dict[str, Any]) -> float:
        """Calculate confidence score based on OCR response."""
        # Base confidence
        confidence = 0.9  # Mistral OCR is generally high quality
        
        # Adjust based on text length (longer text usually means better extraction)
        text_length = len(ocr_response.get("text", ""))
        if text_length < 100:
            confidence -= 0.1
        elif text_length > 1000:
            confidence += 0.05
        
        # Adjust based on presence of structured content
        if ocr_response.get("images"):
            confidence += 0.02
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection based on character patterns."""
        if not text:
            return "unknown"
        
        # Simple heuristics for common languages
        if any(ord(char) > 127 for char in text[:100]):
            # Contains non-ASCII characters
            if any('\u4e00' <= char <= '\u9fff' for char in text[:100]):
                return "zh"  # Chinese
            elif any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text[:100]):
                return "ja"  # Japanese
            elif any('\uac00' <= char <= '\ud7af' for char in text[:100]):
                return "ko"  # Korean
            elif any('\u0600' <= char <= '\u06ff' for char in text[:100]):
                return "ar"  # Arabic
            else:
                return "other"
        else:
            return "en"  # Assume English for ASCII text
    
    def _estimate_page_count(self, text: str) -> int:
        """Estimate page count based on text length."""
        if not text:
            return 0
        
        # Rough estimate: ~500 words per page
        word_count = len(text.split())
        return max(1, word_count // 500)
    
    def _extract_tables_from_markdown(self, markdown: str) -> List[Dict[str, Any]]:
        """Extract table data from markdown content."""
        tables = []
        
        if not markdown:
            return tables
        
        # Simple table extraction from markdown
        lines = markdown.split('\n')
        current_table = None
        table_id = 0
        
        for line in lines:
            line = line.strip()
            if '|' in line and line.startswith('|') and line.endswith('|'):
                if current_table is None:
                    # Start new table
                    table_id += 1
                    current_table = {
                        "table_id": f"mistral_table_{table_id}",
                        "headers": [],
                        "rows": [],
                        "raw_markdown": []
                    }
                
                # Parse table row
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                current_table["raw_markdown"].append(line)
                
                # Check if this is a header separator line
                if all(cell.replace('-', '').replace(':', '').strip() == '' for cell in cells):
                    continue
                
                # Add as header or row
                if not current_table["headers"]:
                    current_table["headers"] = cells
                else:
                    current_table["rows"].append(cells)
            else:
                # End current table if we have one
                if current_table is not None:
                    tables.append(current_table)
                    current_table = None
        
        # Add final table if exists
        if current_table is not None:
            tables.append(current_table)
        
        return tables
    
    def _analyze_document_structure(self, markdown: str) -> Dict[str, Any]:
        """Analyze document structure from markdown."""
        if not markdown:
            return {}
        
        lines = markdown.split('\n')
        structure = {
            "headings": [],
            "paragraphs": 0,
            "lists": 0,
            "tables": 0,
            "code_blocks": 0,
            "images": 0,
            "links": 0
        }
        
        for line in lines:
            line = line.strip()
            
            # Count headings
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                structure["headings"].append({
                    "level": level,
                    "text": line.lstrip('#').strip()
                })
            
            # Count other elements
            elif line and not line.startswith('#'):
                if line.startswith('- ') or line.startswith('* ') or line.startswith('+ '):
                    structure["lists"] += 1
                elif '|' in line and line.startswith('|'):
                    structure["tables"] += 1
                elif line.startswith('```'):
                    structure["code_blocks"] += 1
                elif line.startswith('!['):
                    structure["images"] += 1
                elif '[' in line and '](' in line:
                    structure["links"] += 1
                else:
                    structure["paragraphs"] += 1
        
        return structure

    async def process_with_annotations(
        self,
        document_data: Union[bytes, str],
        document_type: str = "pdf",
        pages: Optional[List[int]] = None,
        bbox_annotation_schema: Optional[Dict[str, Any]] = None,
        document_annotation_schema: Optional[Dict[str, Any]] = None,
        include_image_base64: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process document with structured annotations using Mistral Document AI.

        This method supports the full Mistral Document AI annotation capabilities:
        - BBox annotations for extracting structured data from images/figures
        - Document annotations for extracting structured data from entire documents

        Args:
            document_data: Document data as bytes or base64 string
            document_type: Type of document ("pdf", "image", "docx", "pptx")
            pages: List of page numbers to process (for document annotation, max 8 pages)
            bbox_annotation_schema: JSON schema for bbox annotations
            document_annotation_schema: JSON schema for document annotations
            include_image_base64: Whether to include image base64 in response
            **kwargs: Additional processing options

        Returns:
            OCR results with structured annotations
        """
        try:
            # Prepare document data
            if isinstance(document_data, bytes):
                base64_data = base64.b64encode(document_data).decode('utf-8')
            else:
                base64_data = document_data

            # Validate file size
            estimated_size = len(base64_data) * 3 / 4
            if estimated_size > self.max_file_size:
                raise MistralOCRProcessingError(
                    f"Document size ({estimated_size:.1f}MB) exceeds maximum allowed size (50MB)"
                )

            # Validate page limit for document annotations
            if document_annotation_schema and pages and len(pages) > 8:
                raise MistralOCRProcessingError(
                    "Document annotations are limited to 8 pages maximum"
                )

            # Prepare document URL
            if document_type.lower() in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "avif"]:
                document_url = f"data:image/{document_type};base64,{base64_data}"
                api_document_type = "image_url"
            else:
                if document_type.lower() == "pdf":
                    document_url = f"data:application/pdf;base64,{base64_data}"
                elif document_type.lower() == "docx":
                    document_url = f"data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{base64_data}"
                elif document_type.lower() == "pptx":
                    document_url = f"data:application/vnd.openxmlformats-officedocument.presentationml.presentation;base64,{base64_data}"
                else:
                    document_url = f"data:application/octet-stream;base64,{base64_data}"
                api_document_type = "document_url"

            # Process with Mistral OCR
            start_time = datetime.now()

            ocr_response = await asyncio.wait_for(
                self._process_with_mistral_ocr(
                    document_type=api_document_type,
                    document_url=document_url,
                    include_image_base64=include_image_base64,
                    pages=pages,
                    bbox_annotation_format=bbox_annotation_schema,
                    document_annotation_format=document_annotation_schema
                ),
                timeout=self.timeout_seconds
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            # Structure the response
            result = {
                "success": True,
                "text": ocr_response.get("text", ""),
                "markdown": ocr_response.get("markdown", ""),
                "metadata": {
                    "model": self.model,
                    "processing_time": processing_time,
                    "document_type": document_type,
                    "confidence_score": self._calculate_confidence_score(ocr_response),
                    "language": self._detect_language(ocr_response.get("text", "")),
                    "character_count": len(ocr_response.get("text", "")),
                    "word_count": len(ocr_response.get("text", "").split()),
                    "pages_processed": pages,
                    "usage": ocr_response.get("usage", {}),
                    "has_bbox_annotations": bool(bbox_annotation_schema),
                    "has_document_annotations": bool(document_annotation_schema)
                },
                "images": ocr_response.get("images", []),
                "bbox_annotations": ocr_response.get("bbox_annotations", []),
                "document_annotation": ocr_response.get("document_annotation", {}),
                "tables": self._extract_tables_from_markdown(ocr_response.get("markdown", "")),
                "structure": self._analyze_document_structure(ocr_response.get("markdown", "")),
                "raw_response": ocr_response if kwargs.get("include_raw", False) else None
            }

            logger.info(f"Document annotation processing completed successfully in {processing_time:.2f}s")
            return result

        except asyncio.TimeoutError:
            raise MistralOCRProcessingError(f"OCR processing timed out after {self.timeout_seconds}s")
        except Exception as e:
            logger.error(f"Document annotation processing failed: {e}")
            raise MistralOCRProcessingError(f"Failed to process document with annotations: {str(e)}")

    def create_bbox_annotation_schema(
        self,
        properties: Dict[str, Dict[str, Any]],
        required_fields: Optional[List[str]] = None,
        title: str = "BBoxAnnotation"
    ) -> Dict[str, Any]:
        """
        Create a JSON schema for bbox annotations.

        Args:
            properties: Schema properties with field definitions
            required_fields: List of required field names
            title: Schema title

        Returns:
            JSON schema for bbox annotations
        """
        return {
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    "properties": properties,
                    "required": required_fields or list(properties.keys()),
                    "title": title,
                    "type": "object",
                    "additionalProperties": False
                },
                "name": "bbox_annotation",
                "strict": True
            }
        }

    def create_document_annotation_schema(
        self,
        properties: Dict[str, Dict[str, Any]],
        required_fields: Optional[List[str]] = None,
        title: str = "DocumentAnnotation"
    ) -> Dict[str, Any]:
        """
        Create a JSON schema for document annotations.

        Args:
            properties: Schema properties with field definitions
            required_fields: List of required field names
            title: Schema title

        Returns:
            JSON schema for document annotations
        """
        return {
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    "properties": properties,
                    "required": required_fields or list(properties.keys()),
                    "title": title,
                    "type": "object",
                    "additionalProperties": False
                },
                "name": "document_annotation",
                "strict": True
            }
        }
