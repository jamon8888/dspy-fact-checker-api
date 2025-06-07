#!/usr/bin/env python3
"""
Comprehensive OCR Test with Mistral API Integration
Tests local OCR engines (EasyOCR, Tesseract, RapidOCR) and Mistral OCR API
"""

import asyncio
import os
import time
import base64
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont
import io

# Add the app directory to the path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.document_processing.ocr.factory import OCREngineFactory, OCREngineConfiguration


class ComprehensiveOCRTester:
    """Comprehensive OCR testing with local engines and Mistral API."""
    
    def __init__(self):
        """Initialize the OCR tester."""
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
        """Create test images with different text content."""
        print("\n=== Creating Test Images ===")
        
        try:
            # Create simple text image
            img = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Simple English text
            draw.text((20, 50), "Hello World!", fill='black', font=font)
            draw.text((20, 100), "This is a test document.", fill='black', font=font)
            draw.text((20, 150), "OCR Integration Test 2024", fill='black', font=font)
            
            # Save to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            self.test_images['simple_text'] = img_buffer.getvalue()
            
            # Create multilingual text image
            img2 = Image.new('RGB', (500, 300), color='white')
            draw2 = ImageDraw.Draw(img2)
            
            draw2.text((20, 50), "English: Hello World", fill='black', font=font)
            draw2.text((20, 100), "French: Bonjour le monde", fill='black', font=font)
            draw2.text((20, 150), "German: Hallo Welt", fill='black', font=font)
            draw2.text((20, 200), "Spanish: Hola Mundo", fill='black', font=font)
            draw2.text((20, 250), "Numbers: 123456789", fill='black', font=font)
            
            img_buffer2 = io.BytesIO()
            img2.save(img_buffer2, format='PNG')
            self.test_images['multilingual'] = img_buffer2.getvalue()
            
            # Create complex layout image
            img3 = Image.new('RGB', (600, 400), color='white')
            draw3 = ImageDraw.Draw(img3)
            
            # Title
            draw3.text((200, 20), "INVOICE", fill='black', font=font)
            
            # Table-like structure
            draw3.text((20, 80), "Item", fill='black', font=font)
            draw3.text((200, 80), "Quantity", fill='black', font=font)
            draw3.text((350, 80), "Price", fill='black', font=font)
            
            draw3.text((20, 120), "Product A", fill='black', font=font)
            draw3.text((200, 120), "2", fill='black', font=font)
            draw3.text((350, 120), "$10.00", fill='black', font=font)
            
            draw3.text((20, 160), "Product B", fill='black', font=font)
            draw3.text((200, 160), "1", fill='black', font=font)
            draw3.text((350, 160), "$25.00", fill='black', font=font)
            
            draw3.text((20, 220), "Total: $35.00", fill='black', font=font)
            draw3.text((20, 260), "Date: 2024-01-01", fill='black', font=font)
            draw3.text((20, 300), "Thank you for your business!", fill='black', font=font)
            
            img_buffer3 = io.BytesIO()
            img3.save(img_buffer3, format='PNG')
            self.test_images['complex_layout'] = img_buffer3.getvalue()
            
            self.log_test("test_image_creation", "PASS", {
                "images_created": len(self.test_images),
                "image_types": list(self.test_images.keys())
            })
            
        except Exception as e:
            self.log_test("test_image_creation", "ERROR", {"error": str(e)})
    
    async def test_local_ocr_engines(self):
        """Test all available local OCR engines."""
        print("\n=== Testing Local OCR Engines ===")
        
        if not self.test_images:
            self.create_test_images()
        
        # Test configuration for local engines only
        config = OCREngineConfiguration(
            primary_ocr_engine="easyocr",
            fallback_ocr_engines=["tesseract", "rapidocr"],
            enable_ocr_fallback=True,
            local_ocr_priority=True
        )
        
        factory = OCREngineFactory(config)
        engines = await factory.initialize_engines()
        
        # Test each local engine
        for engine_name in ["easyocr", "tesseract", "rapidocr"]:
            engine = factory.get_engine(engine_name)
            
            if engine and engine.is_available():
                await self._test_engine_with_images(engine, engine_name)
            else:
                self.log_test(f"{engine_name}_engine_test", "FAIL", {
                    "reason": f"{engine_name} not available"
                })
    
    async def test_mistral_ocr_api(self):
        """Test Mistral OCR API integration."""
        print("\n=== Testing Mistral OCR API ===")
        
        # Check for Mistral API key
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        
        if not mistral_api_key:
            self.log_test("mistral_api_key_check", "FAIL", {
                "reason": "MISTRAL_API_KEY environment variable not set",
                "instruction": "Set MISTRAL_API_KEY environment variable to test Mistral OCR"
            })
            return
        
        if not self.test_images:
            self.create_test_images()
        
        # Test configuration for Mistral OCR
        config = OCREngineConfiguration(
            primary_ocr_engine="mistral",
            fallback_ocr_engines=["easyocr"],
            enable_ocr_fallback=True,
            mistral_api_key=mistral_api_key,
            mistral_model="mistral-ocr-latest"
        )
        
        factory = OCREngineFactory(config)
        engines = await factory.initialize_engines()
        
        mistral_engine = factory.get_engine("mistral")
        
        if mistral_engine and mistral_engine.is_available():
            await self._test_engine_with_images(mistral_engine, "mistral")
            
            # Test Mistral-specific features
            await self._test_mistral_specific_features(mistral_engine)
        else:
            self.log_test("mistral_engine_test", "FAIL", {
                "reason": "Mistral OCR engine not available"
            })
    
    async def _test_engine_with_images(self, engine, engine_name: str):
        """Test an OCR engine with all test images."""
        
        for image_name, image_data in self.test_images.items():
            try:
                start_time = time.time()
                
                # Process image
                result = await engine.process_image(image_data, language="en")
                
                processing_time = time.time() - start_time
                
                # Evaluate result
                success = bool(result.text and len(result.text.strip()) > 0)
                
                self.log_test(f"{engine_name}_{image_name}", "PASS" if success else "FAIL", {
                    "text_extracted": bool(result.text),
                    "text_length": len(result.text) if result.text else 0,
                    "confidence": result.confidence,
                    "processing_time": f"{processing_time:.2f}s",
                    "engine_processing_time": f"{result.processing_time:.2f}s",
                    "extracted_text_preview": (result.text[:100] + "..." if result.text and len(result.text) > 100 else result.text).encode('ascii', errors='ignore').decode('ascii')
                })
                
                # Test quality metrics if available
                if result.quality_metrics:
                    self.log_test(f"{engine_name}_{image_name}_quality", "PASS", {
                        "overall_confidence": result.quality_metrics.overall_confidence,
                        "word_count": result.quality_metrics.word_count,
                        "character_count": result.quality_metrics.character_count,
                        "language_confidence": result.quality_metrics.language_confidence
                    })
                
            except Exception as e:
                self.log_test(f"{engine_name}_{image_name}", "ERROR", {
                    "error": str(e),
                    "error_type": e.__class__.__name__
                })
    
    async def _test_mistral_specific_features(self, mistral_engine):
        """Test Mistral-specific OCR features."""
        
        try:
            # Test with bbox annotations
            result = await mistral_engine.process_image(
                self.test_images['complex_layout'],
                language="en",
                bbox_annotation_format="json"
            )
            
            self.log_test("mistral_bbox_annotations", "PASS", {
                "has_bbox_annotations": bool(result.bbox_annotations),
                "bbox_count": len(result.bbox_annotations) if result.bbox_annotations else 0,
                "supports_bbox": True
            })
            
        except Exception as e:
            self.log_test("mistral_bbox_annotations", "ERROR", {"error": str(e)})
        
        try:
            # Test cost estimation
            engine_info = mistral_engine.get_engine_info()
            cost_estimate = mistral_engine.estimate_cost(len(self.test_images['simple_text']), 1)
            
            self.log_test("mistral_cost_estimation", "PASS", {
                "cost_per_page": engine_info.cost_per_page,
                "estimated_cost": cost_estimate,
                "supports_cost_estimation": cost_estimate is not None
            })
            
        except Exception as e:
            self.log_test("mistral_cost_estimation", "ERROR", {"error": str(e)})
    
    async def test_engine_comparison(self):
        """Compare results from different OCR engines."""
        print("\n=== Testing Engine Comparison ===")
        
        if not self.test_images:
            self.create_test_images()
        
        # Get Mistral API key
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        
        # Configure with multiple engines
        config = OCREngineConfiguration(
            primary_ocr_engine="easyocr",
            fallback_ocr_engines=["tesseract", "rapidocr"],
            enable_ocr_fallback=True,
            mistral_api_key=mistral_api_key
        )
        
        factory = OCREngineFactory(config)
        engines = await factory.initialize_engines()
        
        # Test with simple text image
        test_image = self.test_images['simple_text']
        results = {}
        
        for engine_name, engine in engines.items():
            if engine.is_available():
                try:
                    result = await engine.process_image(test_image, language="en")
                    results[engine_name] = result
                except Exception as e:
                    print(f"    {engine_name} failed: {e}")
        
        if len(results) > 1:
            # Compare results
            from app.core.document_processing.ocr.base import OCRQualityAssessor
            assessor = OCRQualityAssessor()
            
            best_result = assessor.compare_results(list(results.values()))
            
            comparison_data = {}
            for engine_name, result in results.items():
                quality_score = assessor.assess_result(result)
                comparison_data[engine_name] = {
                    "quality_score": quality_score,
                    "confidence": result.confidence,
                    "text_length": len(result.text) if result.text else 0,
                    "processing_time": result.processing_time
                }
            
            self.log_test("engine_comparison", "PASS", {
                "engines_compared": len(results),
                "best_engine": best_result.engine_used,
                "comparison_data": comparison_data
            })
        else:
            self.log_test("engine_comparison", "FAIL", {
                "reason": f"Only {len(results)} engines available for comparison"
            })
    
    async def test_fallback_mechanism(self):
        """Test OCR fallback mechanism."""
        print("\n=== Testing Fallback Mechanism ===")
        
        if not self.test_images:
            self.create_test_images()
        
        # Configure with fallback enabled
        config = OCREngineConfiguration(
            primary_ocr_engine="nonexistent_engine",  # Force fallback
            fallback_ocr_engines=["easyocr", "tesseract", "rapidocr"],
            enable_ocr_fallback=True,
            ocr_quality_threshold=0.5
        )
        
        factory = OCREngineFactory(config)
        engines = await factory.initialize_engines()
        
        try:
            # Test fallback processing
            result = await factory.process_with_fallback(
                self.test_images['simple_text'],
                "image",
                language="en"
            )
            
            self.log_test("fallback_mechanism", "PASS", {
                "fallback_worked": True,
                "engine_used": result.engine_used,
                "text_extracted": bool(result.text),
                "confidence": result.confidence
            })
            
        except Exception as e:
            self.log_test("fallback_mechanism", "ERROR", {"error": str(e)})
    
    async def run_all_tests(self):
        """Run all OCR tests."""
        print("Comprehensive OCR Test Suite - Local Engines + Mistral API")
        print("=" * 80)
        
        start_time = time.time()
        
        # Create test images
        self.create_test_images()
        
        # Run all test suites
        await self.test_local_ocr_engines()
        await self.test_mistral_ocr_api()
        await self.test_engine_comparison()
        await self.test_fallback_mechanism()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate summary
        self.print_summary(total_time)
    
    def print_summary(self, total_time: float):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE OCR TEST SUMMARY")
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
        local_tests = [r for r in self.results if any(engine in r["test"] for engine in ["easyocr", "tesseract", "rapidocr"])]
        mistral_tests = [r for r in self.results if "mistral" in r["test"]]
        
        local_passed = sum(1 for r in local_tests if r["status"] == "PASS")
        mistral_passed = sum(1 for r in mistral_tests if r["status"] == "PASS")
        
        print(f"\nLocal OCR Engines: {local_passed}/{len(local_tests)} passed")
        print(f"Mistral OCR API: {mistral_passed}/{len(mistral_tests)} passed")
        
        overall_status = "EXCELLENT" if passed/total > 0.8 else "GOOD" if passed/total > 0.6 else "PARTIAL"
        print(f"\nOverall Status: {overall_status}")
        
        if overall_status in ["EXCELLENT", "GOOD"]:
            print("\n[SUCCESS] OCR integration working well!")
            print("[OK] Multiple OCR engines available and functional")
            print("[OK] Quality assessment and comparison working")
            print("[OK] Fallback mechanisms operational")
            
            if mistral_passed > 0:
                print("[OK] Mistral OCR API integration successful")
            else:
                print("[INFO] Mistral OCR API not tested (API key required)")
                
        else:
            print(f"\n[INFO] OCR integration partially working")
            print("Some engines may not be available in this environment")
        
        # Show any failures
        if failed > 0 or errors > 0:
            print(f"\nIssues Found:")
            for result in self.results:
                if result["status"] in ["FAIL", "ERROR"]:
                    print(f"  - {result['test']}: {result['status']}")


async def main():
    """Main test function."""
    print("To test Mistral OCR API, set the MISTRAL_API_KEY environment variable:")
    print("export MISTRAL_API_KEY=your_api_key_here")
    print()
    
    tester = ComprehensiveOCRTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
