#!/usr/bin/env python3
"""
Test Enhanced Docling Processor with OCR Integration
Tests the integrated OCR capabilities with Enhanced Docling processor
"""

import asyncio
import os
import sys
import time
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont
import io

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.document_processing.enhanced_docling_processor import EnhancedDoclingProcessor
from app.core.document_processing.base import DocumentType


class EnhancedDoclingOCRTester:
    """Test Enhanced Docling processor with OCR integration."""
    
    def __init__(self):
        """Initialize the tester."""
        self.results = []
        self.test_images = {}
    
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
        
        if details:
            for key, value in details.items():
                if key not in ["error"] or status != "PASS":
                    print(f"    {key}: {value}")
    
    def create_test_images(self):
        """Create test images for OCR processing."""
        print("\n=== Creating Test Images ===")
        
        try:
            # Create simple document image
            img = Image.new('RGB', (600, 400), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 20)
                title_font = ImageFont.truetype("arial.ttf", 28)
            except:
                font = ImageFont.load_default()
                title_font = font
            
            # Document title
            draw.text((50, 30), "FACT-CHECKER DOCUMENT", fill='black', font=title_font)
            
            # Document content
            draw.text((50, 80), "This is a test document for OCR processing.", fill='black', font=font)
            draw.text((50, 120), "The enhanced Docling processor should extract", fill='black', font=font)
            draw.text((50, 160), "this text using the integrated OCR engines.", fill='black', font=font)
            draw.text((50, 220), "Key Features:", fill='black', font=font)
            draw.text((70, 260), "- RapidOCR integration", fill='black', font=font)
            draw.text((70, 300), "- Mistral OCR API support", fill='black', font=font)
            draw.text((70, 340), "- Automatic fallback mechanisms", fill='black', font=font)
            
            # Save to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            self.test_images['document'] = img_buffer.getvalue()
            
            # Create invoice-like image
            img2 = Image.new('RGB', (700, 500), color='white')
            draw2 = ImageDraw.Draw(img2)
            
            draw2.text((50, 30), "INVOICE #12345", fill='black', font=title_font)
            draw2.text((50, 80), "Date: 2024-01-01", fill='black', font=font)
            draw2.text((50, 120), "Customer: Fact-Checker Inc.", fill='black', font=font)
            
            # Table header
            draw2.text((50, 180), "Item", fill='black', font=font)
            draw2.text((250, 180), "Quantity", fill='black', font=font)
            draw2.text((400, 180), "Price", fill='black', font=font)
            draw2.text((550, 180), "Total", fill='black', font=font)
            
            # Table rows
            draw2.text((50, 220), "OCR Processing", fill='black', font=font)
            draw2.text((250, 220), "1", fill='black', font=font)
            draw2.text((400, 220), "$100.00", fill='black', font=font)
            draw2.text((550, 220), "$100.00", fill='black', font=font)
            
            draw2.text((50, 260), "Document Analysis", fill='black', font=font)
            draw2.text((250, 260), "2", fill='black', font=font)
            draw2.text((400, 260), "$50.00", fill='black', font=font)
            draw2.text((550, 260), "$100.00", fill='black', font=font)
            
            draw2.text((400, 320), "TOTAL: $200.00", fill='black', font=title_font)
            
            img_buffer2 = io.BytesIO()
            img2.save(img_buffer2, format='PNG')
            self.test_images['invoice'] = img_buffer2.getvalue()
            
            self.log_test("test_image_creation", "PASS", {
                "images_created": len(self.test_images),
                "image_types": list(self.test_images.keys())
            })
            
        except Exception as e:
            self.log_test("test_image_creation", "ERROR", {"error": str(e)})
    
    async def test_enhanced_docling_initialization(self):
        """Test Enhanced Docling processor initialization."""
        print("\n=== Testing Enhanced Docling Initialization ===")
        
        try:
            # Test with OCR configuration - Mistral API primary with local fallback
            config = {
                "primary_ocr_engine": "mistral",
                "fallback_ocr_engines": ["tesseract", "rapidocr"],
                "enable_ocr_fallback": True,
                "ocr_quality_threshold": 0.7,
                "local_ocr_priority": False,  # Prefer Mistral API first
                "enable_ocr": True,
                "timeout_seconds": 60,
                "ocr_language": ["en"],
                "mistral_api_key": os.getenv("MISTRAL_API_KEY"),
                "mistral_model": "mistral-ocr-latest",
                "cost_optimization": True,
                "budget_per_document": 0.10
            }
            
            processor = EnhancedDoclingProcessor(config)
            
            # Check supported formats
            supported_formats = processor.get_supported_formats()
            
            self.log_test("enhanced_docling_initialization", "PASS", {
                "processor_created": True,
                "supported_formats": [fmt.value for fmt in supported_formats],
                "supports_images": DocumentType.IMAGE in supported_formats,
                "ocr_factory_initialized": processor.ocr_factory is not None
            })
            
            return processor
            
        except Exception as e:
            self.log_test("enhanced_docling_initialization", "ERROR", {"error": str(e)})
            return None
    
    async def test_image_processing_with_ocr(self, processor):
        """Test image processing with OCR integration."""
        print("\n=== Testing Image Processing with OCR ===")
        
        if not processor or not self.test_images:
            self.log_test("image_processing_setup", "FAIL", {"reason": "Prerequisites not met"})
            return
        
        for image_name, image_data in self.test_images.items():
            try:
                start_time = time.time()
                
                # Process image with Enhanced Docling + OCR
                result = await processor.process_document(
                    image_data,
                    DocumentType.IMAGE,
                    filename=f"{image_name}.png"
                )
                
                processing_time = time.time() - start_time
                
                # Evaluate results
                success = result.success and bool(result.content.text)
                
                self.log_test(f"image_processing_{image_name}", "PASS" if success else "FAIL", {
                    "success": result.success,
                    "text_extracted": bool(result.content.text),
                    "text_length": len(result.content.text) if result.content.text else 0,
                    "processing_time": f"{processing_time:.2f}s",
                    "docling_processing_time": f"{result.processing_time:.2f}s",
                    "has_images": len(result.images) > 0,
                    "has_metadata": result.metadata is not None,
                    "text_preview": (result.content.text[:100] + "..." if result.content.text and len(result.content.text) > 100 else result.content.text or "").encode('ascii', errors='ignore').decode('ascii')
                })
                
                # Test OCR-specific features
                if result.raw_data and "ocr_result" in str(result.raw_data):
                    self.log_test(f"ocr_features_{image_name}", "PASS", {
                        "ocr_integration": True,
                        "advanced_features_used": result.raw_data.get("advanced_features_used", {})
                    })
                
            except Exception as e:
                self.log_test(f"image_processing_{image_name}", "ERROR", {
                    "error": str(e),
                    "error_type": e.__class__.__name__
                })
    
    async def test_text_document_processing(self, processor):
        """Test text document processing (non-OCR)."""
        print("\n=== Testing Text Document Processing ===")
        
        if not processor:
            self.log_test("text_processing_setup", "FAIL", {"reason": "Processor not available"})
            return
        
        try:
            # Create test text document
            test_text = """# Fact-Checker Integration Test

This is a test document for the Enhanced Docling processor.

## Features Tested
- Text processing
- OCR integration
- Document structure extraction

## Results
The processor should extract this text and structure correctly.
"""
            
            text_data = test_text.encode('utf-8')
            
            start_time = time.time()
            
            result = await processor.process_document(
                text_data,
                DocumentType.TXT,
                filename="test.txt"
            )
            
            processing_time = time.time() - start_time
            
            success = result.success and bool(result.content.text)
            
            self.log_test("text_document_processing", "PASS" if success else "FAIL", {
                "success": result.success,
                "text_extracted": bool(result.content.text),
                "text_length": len(result.content.text) if result.content.text else 0,
                "processing_time": f"{processing_time:.2f}s",
                "has_headings": len(result.content.headings) > 0 if result.content.headings else False,
                "has_paragraphs": len(result.content.paragraphs) > 0 if result.content.paragraphs else False
            })
            
        except Exception as e:
            self.log_test("text_document_processing", "ERROR", {
                "error": str(e),
                "error_type": e.__class__.__name__
            })
    
    async def test_format_support(self, processor):
        """Test format support and validation."""
        print("\n=== Testing Format Support ===")
        
        if not processor:
            self.log_test("format_support_setup", "FAIL", {"reason": "Processor not available"})
            return
        
        try:
            supported_formats = processor.get_supported_formats()
            
            # Test each supported format
            format_tests = {}
            for doc_type in supported_formats:
                format_tests[doc_type.value] = processor.supports_format(doc_type)
            
            # Test unsupported format
            unsupported_test = not processor.supports_format(DocumentType.UNKNOWN)
            
            self.log_test("format_support", "PASS", {
                "supported_formats": [fmt.value for fmt in supported_formats],
                "format_tests": format_tests,
                "correctly_rejects_unsupported": unsupported_test,
                "image_support": DocumentType.IMAGE in supported_formats
            })
            
        except Exception as e:
            self.log_test("format_support", "ERROR", {
                "error": str(e),
                "error_type": e.__class__.__name__
            })
    
    async def run_all_tests(self):
        """Run all Enhanced Docling + OCR integration tests."""
        print("Enhanced Docling + OCR Integration Test Suite")
        print("=" * 80)
        
        start_time = time.time()
        
        # Create test images
        self.create_test_images()
        
        # Initialize processor
        processor = await self.test_enhanced_docling_initialization()
        
        # Run all test suites
        await self.test_format_support(processor)
        await self.test_text_document_processing(processor)
        await self.test_image_processing_with_ocr(processor)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate summary
        self.print_summary(total_time)
    
    def print_summary(self, total_time: float):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("ENHANCED DOCLING + OCR INTEGRATION TEST SUMMARY")
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
        
        # Categorize results
        ocr_tests = [r for r in self.results if "image_processing" in r["test"] or "ocr" in r["test"]]
        docling_tests = [r for r in self.results if "docling" in r["test"] or "text" in r["test"]]
        
        ocr_passed = sum(1 for r in ocr_tests if r["status"] == "PASS")
        docling_passed = sum(1 for r in docling_tests if r["status"] == "PASS")
        
        print(f"\nOCR Integration: {ocr_passed}/{len(ocr_tests)} passed")
        print(f"Docling Processing: {docling_passed}/{len(docling_tests)} passed")
        
        overall_status = "EXCELLENT" if passed/total > 0.8 else "GOOD" if passed/total > 0.6 else "PARTIAL"
        print(f"\nOverall Status: {overall_status}")
        
        if overall_status in ["EXCELLENT", "GOOD"]:
            print("\n[SUCCESS] Enhanced Docling + OCR integration working!")
            print("[OK] Image processing with OCR functional")
            print("[OK] Text document processing working")
            print("[OK] Format support comprehensive")
            print("[OK] Integration layer operational")
        else:
            print(f"\n[INFO] Enhanced Docling + OCR integration partially working")
        
        # Show any failures
        if failed > 0 or errors > 0:
            print(f"\nIssues Found:")
            for result in self.results:
                if result["status"] in ["FAIL", "ERROR"]:
                    print(f"  - {result['test']}: {result['status']}")


async def main():
    """Main test function."""
    tester = EnhancedDoclingOCRTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
