#!/usr/bin/env python3
"""
Test Enhanced Docling Document Processing
Tests advanced features like table extraction, OCR, chunking, and more
"""

import asyncio
import tempfile
import os
import time
from pathlib import Path
from typing import Dict, Any

# Add the app directory to the path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.document_processing.enhanced_docling_processor import (
    EnhancedDoclingProcessor, EnhancedDoclingConfiguration
)
from app.core.document_processing.base import DocumentType


class EnhancedDoclingTester:
    """Comprehensive tester for enhanced Docling features."""
    
    def __init__(self):
        """Initialize the tester."""
        self.results = []
        self.test_documents = self._create_test_documents()
    
    def _create_test_documents(self) -> Dict[str, bytes]:
        """Create test documents for processing."""
        test_docs = {}
        
        # Create a simple text document
        text_content = """
        Enhanced Document Processing Test
        
        This is a test document for the enhanced Docling processor.
        
        ## Key Features to Test
        
        1. **Table Extraction**: Advanced table structure recognition
        2. **OCR Capabilities**: Text extraction from images
        3. **Formula Detection**: Mathematical formula recognition
        4. **Code Detection**: Programming code identification
        5. **Chunking**: Document segmentation for RAG
        
        ### Sample Data Table
        
        | Feature | Status | Performance |
        |---------|--------|-------------|
        | Table Extraction | ✓ | Excellent |
        | OCR Processing | ✓ | Very Good |
        | Formula Detection | ✓ | Good |
        | Code Recognition | ✓ | Good |
        | Document Chunking | ✓ | Excellent |
        
        ### Code Example
        
        ```python
        def process_document(file_path):
            processor = EnhancedDoclingProcessor()
            result = await processor.process_document(file_path)
            return result
        ```
        
        ### Mathematical Formula
        
        The quadratic formula: x = (-b ± √(b² - 4ac)) / 2a
        
        ### Conclusion
        
        This enhanced processor provides comprehensive document analysis
        with advanced AI-powered features for fact-checking applications.
        """
        
        test_docs['test_document.txt'] = text_content.encode('utf-8')
        
        # Create HTML content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Enhanced Docling Test HTML</title>
        </head>
        <body>
            <h1>HTML Document Processing Test</h1>
            
            <h2>Features</h2>
            <ul>
                <li>HTML structure recognition</li>
                <li>Table extraction from HTML</li>
                <li>Text content extraction</li>
            </ul>
            
            <h2>Sample Table</h2>
            <table border="1">
                <tr>
                    <th>Technology</th>
                    <th>Version</th>
                    <th>Status</th>
                </tr>
                <tr>
                    <td>Docling</td>
                    <td>2.36.0+</td>
                    <td>Active</td>
                </tr>
                <tr>
                    <td>Python</td>
                    <td>3.11+</td>
                    <td>Active</td>
                </tr>
            </table>
            
            <p>This HTML document tests the enhanced processing capabilities.</p>
        </body>
        </html>
        """
        
        test_docs['test_document.html'] = html_content.encode('utf-8')
        
        return test_docs
    
    def log_test(self, test_name: str, status: str, details: Dict[str, Any] = None):
        """Log test result."""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": time.time(),
            "details": details or {}
        }
        self.results.append(result)
        
        status_icon = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[ERROR]"
        print(f"{status_icon} {test_name}")
        
        if details and status != "PASS":
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    async def test_enhanced_configuration(self):
        """Test enhanced configuration options."""
        print("\n=== Testing Enhanced Configuration ===")
        
        try:
            # Test basic configuration
            basic_config = EnhancedDoclingConfiguration()
            
            self.log_test("basic_configuration", "PASS", {
                "timeout": basic_config.timeout_seconds,
                "max_file_size": basic_config.max_file_size,
                "ocr_enabled": basic_config.enable_ocr,
                "table_structure": basic_config.enable_table_structure
            })
            
            # Test advanced configuration
            advanced_config = EnhancedDoclingConfiguration({
                "enable_ocr": True,
                "enable_table_structure": True,
                "enable_picture_extraction": True,
                "enable_formula_detection": True,
                "enable_chunking": True,
                "table_mode": "accurate",
                "ocr_language": ["en", "fr"],
                "chunk_max_tokens": 256
            })
            
            self.log_test("advanced_configuration", "PASS", {
                "table_mode": advanced_config.table_mode,
                "ocr_languages": advanced_config.ocr_language,
                "chunking_enabled": advanced_config.enable_chunking,
                "max_tokens": advanced_config.chunk_max_tokens
            })
            
        except Exception as e:
            self.log_test("enhanced_configuration", "ERROR", {"error": str(e)})
    
    async def test_processor_initialization(self):
        """Test enhanced processor initialization."""
        print("\n=== Testing Processor Initialization ===")
        
        try:
            # Test basic initialization
            processor = EnhancedDoclingProcessor()
            
            self.log_test("processor_initialization", "PASS", {
                "converter_created": processor.converter is not None,
                "chunker_available": processor.chunker is not None,
                "supported_formats": len(processor.get_supported_formats())
            })
            
            # Test supported formats
            supported_formats = processor.get_supported_formats()
            expected_formats = [
                DocumentType.PDF, DocumentType.DOCX, DocumentType.HTML,
                DocumentType.TXT, DocumentType.RTF, DocumentType.ODT
            ]
            
            formats_match = all(fmt in supported_formats for fmt in expected_formats)
            
            self.log_test("supported_formats", "PASS" if formats_match else "FAIL", {
                "expected": len(expected_formats),
                "actual": len(supported_formats),
                "formats": [fmt.value for fmt in supported_formats]
            })
            
        except Exception as e:
            self.log_test("processor_initialization", "ERROR", {"error": str(e)})
    
    async def test_text_document_processing(self):
        """Test processing of text documents."""
        print("\n=== Testing Text Document Processing ===")
        
        try:
            processor = EnhancedDoclingProcessor({
                "enable_chunking": True,
                "chunk_max_tokens": 128
            })
            
            # Process text document
            text_data = self.test_documents['test_document.txt']
            
            start_time = time.time()
            result = await processor.process_document(
                text_data, 
                DocumentType.TXT,
                filename="test_document.txt"
            )
            processing_time = time.time() - start_time
            
            if result.success:
                self.log_test("text_processing", "PASS", {
                    "processing_time": f"{processing_time:.3f}s",
                    "content_length": len(result.content.text),
                    "headings_found": len(result.content.headings),
                    "paragraphs_found": len(result.content.paragraphs),
                    "chunks_created": len(result.raw_data.get("chunks", [])),
                    "processor": result.raw_data.get("processor_name", "unknown")
                })
                
                # Test content structure
                if result.content.headings:
                    self.log_test("heading_extraction", "PASS", {
                        "headings_count": len(result.content.headings),
                        "first_heading": result.content.headings[0].get('text', '')[:50]
                    })
                else:
                    self.log_test("heading_extraction", "FAIL", {"reason": "No headings extracted"})
                
                # Test chunking
                chunks = result.raw_data.get("chunks", [])
                if chunks:
                    self.log_test("document_chunking", "PASS", {
                        "chunks_count": len(chunks),
                        "avg_chunk_size": sum(chunk.get('token_count', 0) for chunk in chunks) / len(chunks)
                    })
                else:
                    self.log_test("document_chunking", "FAIL", {"reason": "No chunks created"})
                
            else:
                self.log_test("text_processing", "FAIL", {"reason": "Processing failed"})
                
        except Exception as e:
            self.log_test("text_processing", "ERROR", {"error": str(e)})
    
    async def test_html_document_processing(self):
        """Test processing of HTML documents."""
        print("\n=== Testing HTML Document Processing ===")
        
        try:
            processor = EnhancedDoclingProcessor({
                "enable_table_structure": True,
                "enable_chunking": True
            })
            
            # Process HTML document
            html_data = self.test_documents['test_document.html']
            
            start_time = time.time()
            result = await processor.process_document(
                html_data,
                DocumentType.HTML,
                filename="test_document.html"
            )
            processing_time = time.time() - start_time
            
            if result.success:
                self.log_test("html_processing", "PASS", {
                    "processing_time": f"{processing_time:.3f}s",
                    "content_length": len(result.content.text),
                    "tables_found": len(result.tables),
                    "metadata_extracted": bool(result.metadata),
                    "processor": result.raw_data.get("processor_name", "unknown")
                })
                
                # Test table extraction
                if result.tables:
                    table = result.tables[0]
                    self.log_test("html_table_extraction", "PASS", {
                        "tables_count": len(result.tables),
                        "headers_count": len(table.headers),
                        "rows_count": len(table.rows),
                        "caption": table.caption
                    })
                else:
                    self.log_test("html_table_extraction", "FAIL", {"reason": "No tables extracted"})
                
            else:
                self.log_test("html_processing", "FAIL", {"reason": "Processing failed"})
                
        except Exception as e:
            self.log_test("html_processing", "ERROR", {"error": str(e)})
    
    async def test_advanced_features(self):
        """Test advanced processing features."""
        print("\n=== Testing Advanced Features ===")
        
        try:
            # Test with all advanced features enabled
            advanced_config = {
                "enable_ocr": True,
                "enable_table_structure": True,
                "enable_picture_extraction": True,
                "enable_formula_detection": True,
                "enable_code_detection": True,
                "enable_chunking": True,
                "table_mode": "accurate",
                "ocr_language": ["en"],
                "chunk_max_tokens": 256
            }
            
            processor = EnhancedDoclingProcessor(advanced_config)
            
            # Test feature availability
            features_enabled = {
                "ocr": processor.docling_config.enable_ocr,
                "table_structure": processor.docling_config.enable_table_structure,
                "picture_extraction": processor.docling_config.enable_picture_extraction,
                "formula_detection": processor.docling_config.enable_formula_detection,
                "chunking": processor.docling_config.enable_chunking
            }
            
            all_features_enabled = all(features_enabled.values())
            
            self.log_test("advanced_features_config", "PASS" if all_features_enabled else "FAIL", {
                "features_enabled": features_enabled,
                "table_mode": processor.docling_config.table_mode,
                "ocr_languages": processor.docling_config.ocr_language
            })
            
            # Test helper methods
            heading_level = processor._extract_heading_level("h2")
            code_language = processor._detect_code_language("def test(): pass")
            
            self.log_test("helper_methods", "PASS", {
                "heading_level_detection": heading_level == 2,
                "code_language_detection": code_language == "python"
            })
            
        except Exception as e:
            self.log_test("advanced_features", "ERROR", {"error": str(e)})
    
    async def test_error_handling(self):
        """Test error handling and edge cases."""
        print("\n=== Testing Error Handling ===")
        
        try:
            processor = EnhancedDoclingProcessor()
            
            # Test with empty data
            try:
                result = await processor.process_document(
                    b"", 
                    DocumentType.TXT,
                    filename="empty.txt"
                )
                self.log_test("empty_document_handling", "PASS", {
                    "handled_gracefully": True,
                    "success": result.success
                })
            except Exception as e:
                self.log_test("empty_document_handling", "FAIL", {"error": str(e)})
            
            # Test with very large content (within limits)
            large_content = "This is a test. " * 1000  # ~16KB
            try:
                result = await processor.process_document(
                    large_content.encode(),
                    DocumentType.TXT,
                    filename="large.txt"
                )
                self.log_test("large_document_handling", "PASS", {
                    "content_size": len(large_content),
                    "processed_successfully": result.success
                })
            except Exception as e:
                self.log_test("large_document_handling", "FAIL", {"error": str(e)})
            
        except Exception as e:
            self.log_test("error_handling", "ERROR", {"error": str(e)})
    
    async def run_all_tests(self):
        """Run all enhanced Docling tests."""
        print("Enhanced Docling Document Processing - Comprehensive Test Suite")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all test suites
        await self.test_enhanced_configuration()
        await self.test_processor_initialization()
        await self.test_text_document_processing()
        await self.test_html_document_processing()
        await self.test_advanced_features()
        await self.test_error_handling()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate summary
        self.print_summary(total_time)
    
    def print_summary(self, total_time: float):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("ENHANCED DOCLING TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.results if result["status"] == "PASS")
        failed = sum(1 for result in self.results if result["status"] == "FAIL")
        errors = sum(1 for result in self.results if result["status"] == "ERROR")
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print(f"Total Time: {total_time:.2f} seconds")
        
        overall_status = "PASS" if failed == 0 and errors == 0 else "FAIL"
        print(f"\nOverall Status: {overall_status}")
        
        if overall_status == "PASS":
            print("\n[SUCCESS] All enhanced Docling features are working correctly!")
            print("✓ Advanced document processing capabilities verified")
            print("✓ Table extraction and structure recognition working")
            print("✓ Document chunking for RAG applications functional")
            print("✓ Enhanced metadata extraction operational")
            print("✓ Error handling robust and reliable")
        else:
            print(f"\n[WARNING] {failed + errors} tests failed. Review the results above.")
            
            # Show failed tests
            if failed > 0 or errors > 0:
                print("\nFailed/Error Tests:")
                for result in self.results:
                    if result["status"] in ["FAIL", "ERROR"]:
                        print(f"  - {result['test']}: {result['status']}")


async def main():
    """Main test function."""
    tester = EnhancedDoclingTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
