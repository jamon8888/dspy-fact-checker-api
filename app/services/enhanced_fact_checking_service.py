#!/usr/bin/env python3
"""
Enhanced Fact-Checking Service with Integrated Document Processing
Connects enhanced Docling processor with DSPy fact-checking pipeline
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime
import uuid

from app.core.document_processing.base import DocumentType
from app.core.document_processing.enhanced_docling_processor import (
    EnhancedDoclingProcessor, DOCLING_AVAILABLE
)
from app.services.dspy_fact_checking_service import DSPyFactCheckingService
from app.services.document_service import DocumentProcessingService

logger = logging.getLogger(__name__)


class EnhancedFactCheckingService:
    """Enhanced fact-checking service with integrated document processing."""
    
    def __init__(self):
        """Initialize enhanced fact-checking service."""
        self.document_service = DocumentProcessingService()
        self.dspy_service = DSPyFactCheckingService()
        self.enhanced_processor = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize the enhanced fact-checking service."""
        try:
            # Initialize DSPy service
            await self.dspy_service.initialize()
            
            # Initialize enhanced Docling processor
            if DOCLING_AVAILABLE:
                enhanced_config = {
                    "enable_ocr": True,
                    "enable_table_structure": True,
                    "enable_picture_extraction": True,
                    "enable_formula_detection": True,
                    "enable_code_detection": True,
                    "enable_chunking": True,
                    "table_mode": "accurate",
                    "ocr_language": ["en"],
                    "chunk_max_tokens": 512,
                    "timeout_seconds": 300,
                    "max_file_size": 100 * 1024 * 1024,  # 100MB
                    "max_pages": 1000
                }
                
                self.enhanced_processor = EnhancedDoclingProcessor(enhanced_config)
                logger.info("Enhanced Docling processor initialized for fact-checking")
            
            self.initialized = True
            logger.info("Enhanced fact-checking service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced fact-checking service: {e}")
            self.initialized = False
    
    async def fact_check_document(
        self,
        file_data: Union[bytes, BinaryIO],
        filename: str,
        document_type: str = "general",
        confidence_threshold: float = 0.5,
        max_claims_per_document: int = 50,
        enable_uncertainty_quantification: bool = True,
        preserve_context: bool = True,
        extract_citations: bool = True,
        verification_depth: str = "standard",
        require_multiple_sources: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform comprehensive fact-checking on a document using enhanced processing.
        
        Args:
            file_data: Document data
            filename: Original filename
            document_type: Type of document for specialized analysis
            confidence_threshold: Minimum confidence for claims
            max_claims_per_document: Maximum claims to extract
            enable_uncertainty_quantification: Enable uncertainty analysis
            preserve_context: Preserve document context in results
            extract_citations: Extract citations and references
            verification_depth: Depth of verification ("standard", "deep", "comprehensive")
            require_multiple_sources: Require multiple sources for verification
            **kwargs: Additional processing options
            
        Returns:
            Comprehensive fact-checking results
        """
        if not self.initialized:
            await self.initialize()
        
        processing_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting enhanced fact-checking for document: {filename}")
            
            # Step 1: Enhanced document processing
            document_result = await self._process_document_enhanced(
                file_data, filename, **kwargs
            )
            
            if not document_result["success"]:
                raise Exception(f"Document processing failed: {document_result.get('error')}")
            
            # Step 2: Extract structured content for fact-checking
            structured_content = self._prepare_content_for_fact_checking(document_result)
            
            # Step 3: Perform DSPy fact-checking with enhanced context
            fact_check_result = await self.dspy_service.fact_check_document(
                document_content=structured_content["main_text"],
                document_metadata=structured_content["metadata"],
                document_type=document_type,
                confidence_threshold=confidence_threshold,
                max_claims_per_document=max_claims_per_document,
                enable_uncertainty_quantification=enable_uncertainty_quantification,
                preserve_context=preserve_context,
                extract_citations=extract_citations,
                verification_depth=verification_depth,
                require_multiple_sources=require_multiple_sources,
                **kwargs
            )
            
            # Step 4: Enhance results with document structure information
            enhanced_result = self._enhance_fact_check_results(
                fact_check_result, document_result, structured_content
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "processing_id": processing_id,
                "filename": filename,
                "success": True,
                "processing_time": processing_time,
                "document_processing": document_result,
                "fact_checking": enhanced_result,
                "enhanced_features": {
                    "advanced_document_processing": True,
                    "structured_content_analysis": True,
                    "context_aware_fact_checking": True,
                    "multi_modal_processing": document_result.get("tables") or document_result.get("images")
                },
                "processed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Enhanced fact-checking failed for {filename}: {e}")
            
            return {
                "processing_id": processing_id,
                "filename": filename,
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "processed_at": datetime.now().isoformat()
            }
    
    async def fact_check_text_with_context(
        self,
        text: str,
        context_metadata: Optional[Dict[str, Any]] = None,
        document_type: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fact-check text with optional context metadata.
        
        Args:
            text: Text content to fact-check
            context_metadata: Optional context information
            document_type: Type of document for specialized analysis
            **kwargs: Additional fact-checking options
            
        Returns:
            Fact-checking results with enhanced context
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Prepare enhanced metadata
            enhanced_metadata = context_metadata or {}
            enhanced_metadata.update({
                "processing_method": "enhanced_text_analysis",
                "document_type": document_type,
                "text_length": len(text),
                "processing_timestamp": datetime.now().isoformat()
            })
            
            # Perform fact-checking with DSPy
            result = await self.dspy_service.fact_check_document(
                document_content=text,
                document_metadata=enhanced_metadata,
                document_type=document_type,
                **kwargs
            )
            
            return {
                "success": True,
                "text_length": len(text),
                "fact_checking": result,
                "enhanced_features": {
                    "context_aware_analysis": True,
                    "metadata_enrichment": True
                },
                "processed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Enhanced text fact-checking failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
    
    async def _process_document_enhanced(
        self,
        file_data: Union[bytes, BinaryIO],
        filename: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Process document using enhanced Docling processor."""
        try:
            if self.enhanced_processor:
                # Use enhanced processor directly
                file_type = self._get_document_type(filename)
                
                result = await self.enhanced_processor.process_document(
                    file_data=file_data,
                    file_type=file_type,
                    filename=filename,
                    **kwargs
                )
                
                return {
                    "success": result.success,
                    "content": result.content,
                    "metadata": result.metadata,
                    "tables": result.tables,
                    "images": result.images,
                    "processing_time": result.processing_time,
                    "processor_used": "enhanced_docling",
                    "raw_data": result.raw_data
                }
            else:
                # Fallback to document service
                return await self.document_service.process_document(
                    file_data=file_data,
                    filename=filename,
                    processor_name="docling",
                    **kwargs
                )
                
        except Exception as e:
            logger.error(f"Enhanced document processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "processor_used": "fallback"
            }
    
    def _prepare_content_for_fact_checking(self, document_result: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare processed document content for fact-checking."""
        try:
            content = document_result.get("content", {})
            metadata = document_result.get("metadata", {})
            
            # Extract main text
            if hasattr(content, 'text'):
                main_text = content.text
            elif isinstance(content, dict):
                main_text = content.get("text", "")
            else:
                main_text = str(content)
            
            # Prepare enhanced metadata
            enhanced_metadata = {
                "original_filename": metadata.get("title", "Unknown"),
                "document_author": metadata.get("author", "Unknown"),
                "page_count": metadata.get("page_count", 0),
                "word_count": metadata.get("word_count", 0),
                "language": metadata.get("language", "unknown"),
                "document_classification": metadata.get("custom_properties", {}).get("document_type", "general"),
                "processing_method": "enhanced_docling",
                "has_tables": len(document_result.get("tables", [])) > 0,
                "has_images": len(document_result.get("images", [])) > 0,
                "chunks_available": len(document_result.get("raw_data", {}).get("chunks", [])) > 0
            }
            
            return {
                "main_text": main_text,
                "metadata": enhanced_metadata,
                "structured_content": content,
                "tables": document_result.get("tables", []),
                "images": document_result.get("images", []),
                "chunks": document_result.get("raw_data", {}).get("chunks", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to prepare content for fact-checking: {e}")
            return {
                "main_text": "",
                "metadata": {},
                "structured_content": {},
                "tables": [],
                "images": [],
                "chunks": []
            }
    
    def _enhance_fact_check_results(
        self,
        fact_check_result: Dict[str, Any],
        document_result: Dict[str, Any],
        structured_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance fact-checking results with document structure information."""
        try:
            enhanced_result = fact_check_result.copy()
            
            # Add document structure context
            enhanced_result["document_context"] = {
                "structure_analysis": {
                    "total_pages": structured_content["metadata"].get("page_count", 0),
                    "total_words": structured_content["metadata"].get("word_count", 0),
                    "tables_count": len(structured_content["tables"]),
                    "images_count": len(structured_content["images"]),
                    "chunks_count": len(structured_content["chunks"])
                },
                "processing_metadata": {
                    "processor_used": document_result.get("processor_used", "unknown"),
                    "processing_time": document_result.get("processing_time", 0),
                    "advanced_features_used": document_result.get("raw_data", {}).get("advanced_features_used", {})
                }
            }
            
            # Add chunk-based analysis if available
            if structured_content["chunks"]:
                enhanced_result["chunk_analysis"] = {
                    "total_chunks": len(structured_content["chunks"]),
                    "avg_chunk_size": sum(chunk.get("token_count", 0) for chunk in structured_content["chunks"]) / len(structured_content["chunks"]),
                    "page_coverage": list(set(
                        page for chunk in structured_content["chunks"] 
                        for page in chunk.get("page_references", [])
                    ))
                }
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Failed to enhance fact-check results: {e}")
            return fact_check_result
    
    def _get_document_type(self, filename: str) -> DocumentType:
        """Get document type from filename."""
        try:
            extension = filename.lower().split('.')[-1]
            
            type_mapping = {
                'pdf': DocumentType.PDF,
                'docx': DocumentType.DOCX,
                'doc': DocumentType.DOCX,  # Treat as DOCX
                'html': DocumentType.HTML,
                'htm': DocumentType.HTML,
                'txt': DocumentType.TXT,
                'rtf': DocumentType.RTF,
                'odt': DocumentType.ODT
            }
            
            return type_mapping.get(extension, DocumentType.TXT)
            
        except Exception:
            return DocumentType.TXT


# Global service instance
enhanced_fact_checking_service = EnhancedFactCheckingService()
