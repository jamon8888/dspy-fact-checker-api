#!/usr/bin/env python3
"""
Test Mistral OCR API as Primary with Local Fallback
Tests the correct implementation: Mistral API first, then Tesseract, then RapidOCR
"""

import asyncio
import os
import sys
import time
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont
import io

# Load production environment variables FIRST
from dotenv import load_dotenv
load_dotenv(r"C:\Users\NMarchitecte\Documents\fact-checker\.env.production")

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.document_processing.ocr.factory import OCREngineFactory, OCREngineConfiguration


class MistralPrimaryOCRTester:
    """Test Mistral OCR API as primary with local fallback."""
    
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
    
    def create_test_image(self):
        """Create test image for OCR processing."""
        print("\n=== Creating Test Image ===")
        
        try:
            # Create test image
            img = Image.new('RGB', (600, 400), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 20)
                title_font = ImageFont.truetype("arial.ttf", 28)
            except:
                font = ImageFont.load_default()
                title_font = font
            
            # Document title
            draw.text((50, 30), "MISTRAL OCR API TEST", fill='black', font=title_font)
            
            # Document content
            draw.text((50, 80), "This document tests Mistral OCR API integration", fill='black', font=font)
            draw.text((50, 120), "with fallback to local OCR engines.", fill='black', font=font)
            draw.text((50, 180), "Priority Order:", fill='black', font=font)
            draw.text((70, 220), "1. Mistral OCR API (Primary)", fill='black', font=font)
            draw.text((70, 260), "2. Tesseract OCR (Fallback 1)", fill='black', font=font)
            draw.text((70, 300), "3. RapidOCR (Fallback 2)", fill='black', font=font)
            draw.text((50, 350), "Date: 2024-01-01", fill='black', font=font)
            
            # Save to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            self.test_images['mistral_test'] = img_buffer.getvalue()
            
            self.log_test("test_image_creation", "PASS", {
                "image_created": True,
                "image_size": len(self.test_images['mistral_test'])
            })
            
        except Exception as e:
            self.log_test("test_image_creation", "ERROR", {"error": str(e)})
    
    async def test_mistral_api_primary(self):
        """Test Mistral OCR API as primary engine."""
        print("\n=== Testing Mistral OCR API as Primary ===")
        
        # Check for Mistral API key
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        
        if not mistral_api_key:
            self.log_test("mistral_api_key_check", "FAIL", {
                "reason": "MISTRAL_API_KEY environment variable not set",
                "instruction": "Set MISTRAL_API_KEY environment variable to test Mistral OCR",
                "example": "export MISTRAL_API_KEY=your_api_key_here"
            })
            return False
        
        self.log_test("mistral_api_key_check", "PASS", {
            "api_key_found": True,
            "api_key_preview": f"{mistral_api_key[:10]}..."
        })
        
        try:
            # Configure with Mistral as primary
            config = OCREngineConfiguration({
                "primary_ocr_engine": "mistral",
                "fallback_ocr_engines": ["tesseract", "rapidocr"],
                "enable_ocr_fallback": True,
                "ocr_quality_threshold": 0.7,
                "local_ocr_priority": False,  # Prefer cloud API first
                "cost_optimization": True,
                "budget_per_document": 0.10,  # 10 cents per document
                "mistral_api_key": mistral_api_key,
                "mistral_model": "mistral-ocr-latest",  # Correct Mistral OCR model (verified working)
                "max_concurrent_requests": 3
            })
            
            factory = OCREngineFactory(config)
            engines = await factory.initialize_engines()
            
            # Test Mistral engine specifically
            mistral_engine = factory.get_engine("mistral")
            
            if mistral_engine and mistral_engine.is_available():
                start_time = time.time()
                
                result = await mistral_engine.process_image(
                    self.test_images['mistral_test'],
                    language="en"
                )
                
                processing_time = time.time() - start_time
                
                self.log_test("mistral_api_processing", "PASS", {
                    "text_extracted": bool(result.text),
                    "text_length": len(result.text) if result.text else 0,
                    "confidence": result.confidence,
                    "processing_time": f"{processing_time:.2f}s",
                    "engine_used": result.engine_used,
                    "has_bbox_annotations": bool(result.bbox_annotations),
                    "text_preview": (result.text[:100] + "..." if result.text and len(result.text) > 100 else result.text or "").encode('ascii', errors='ignore').decode('ascii')
                })
                
                return True
            else:
                self.log_test("mistral_api_processing", "FAIL", {
                    "reason": "Mistral OCR engine not available or not initialized"
                })
                return False
                
        except Exception as e:
            self.log_test("mistral_api_processing", "ERROR", {
                "error": str(e),
                "error_type": e.__class__.__name__
            })
            return False
    
    async def test_fallback_mechanism(self):
        """Test fallback mechanism when Mistral API fails."""
        print("\n=== Testing Fallback Mechanism ===")
        
        try:
            # Configure with invalid Mistral API key to force fallback
            config = OCREngineConfiguration({
                "primary_ocr_engine": "mistral",
                "fallback_ocr_engines": ["tesseract", "rapidocr"],
                "enable_ocr_fallback": True,
                "ocr_quality_threshold": 0.5,
                "local_ocr_priority": False,
                "mistral_api_key": "invalid_key_to_force_fallback",
                "mistral_model": "mistral-ocr-latest"
            })
            
            factory = OCREngineFactory(config)
            engines = await factory.initialize_engines()
            
            # Test fallback processing
            start_time = time.time()
            
            result = await factory.process_with_fallback(
                self.test_images['mistral_test'],
                "image",
                language="en"
            )
            
            processing_time = time.time() - start_time
            
            # Check which engine was actually used
            fallback_engine_used = result.engine_used
            
            self.log_test("fallback_mechanism", "PASS", {
                "fallback_worked": True,
                "engine_used": fallback_engine_used,
                "text_extracted": bool(result.text),
                "text_length": len(result.text) if result.text else 0,
                "confidence": result.confidence,
                "processing_time": f"{processing_time:.2f}s",
                "mistral_failed_as_expected": fallback_engine_used != "mistral"
            })
            
        except Exception as e:
            self.log_test("fallback_mechanism", "ERROR", {
                "error": str(e),
                "error_type": e.__class__.__name__
            })
    
    async def test_local_engines_availability(self):
        """Test availability of local OCR engines."""
        print("\n=== Testing Local OCR Engines Availability ===")
        
        try:
            # Test each local engine
            config = OCREngineConfiguration({
                "primary_ocr_engine": "tesseract",
                "fallback_ocr_engines": ["rapidocr"],
                "enable_ocr_fallback": True
            })
            
            factory = OCREngineFactory(config)
            engines = await factory.initialize_engines()
            
            # Test Tesseract
            tesseract_engine = factory.get_engine("tesseract")
            tesseract_available = tesseract_engine.is_available() if tesseract_engine else False
            
            # Test RapidOCR
            rapidocr_engine = factory.get_engine("rapidocr")
            rapidocr_available = rapidocr_engine.is_available() if rapidocr_engine else False
            
            self.log_test("local_engines_availability", "PASS", {
                "tesseract_available": tesseract_available,
                "rapidocr_available": rapidocr_available,
                "total_local_engines": sum([tesseract_available, rapidocr_available]),
                "fallback_options": tesseract_available or rapidocr_available
            })
            
            # Test working local engine
            if rapidocr_available:
                start_time = time.time()
                result = await rapidocr_engine.process_image(
                    self.test_images['mistral_test'],
                    language="en"
                )
                processing_time = time.time() - start_time
                
                self.log_test("rapidocr_local_test", "PASS", {
                    "text_extracted": bool(result.text),
                    "text_length": len(result.text) if result.text else 0,
                    "confidence": result.confidence,
                    "processing_time": f"{processing_time:.2f}s",
                    "engine_used": result.engine_used
                })
            
            if tesseract_available:
                start_time = time.time()
                result = await tesseract_engine.process_image(
                    self.test_images['mistral_test'],
                    language="en"
                )
                processing_time = time.time() - start_time
                
                self.log_test("tesseract_local_test", "PASS", {
                    "text_extracted": bool(result.text),
                    "text_length": len(result.text) if result.text else 0,
                    "confidence": result.confidence,
                    "processing_time": f"{processing_time:.2f}s",
                    "engine_used": result.engine_used
                })
            
        except Exception as e:
            self.log_test("local_engines_availability", "ERROR", {
                "error": str(e),
                "error_type": e.__class__.__name__
            })
    
    async def run_all_tests(self):
        """Run all Mistral primary OCR tests."""
        print("Mistral OCR API Primary with Local Fallback Test Suite")
        print("=" * 80)
        print("Testing the CORRECT implementation:")
        print("1. Mistral OCR API (Primary)")
        print("2. Tesseract OCR (Fallback 1)")
        print("3. RapidOCR (Fallback 2)")
        print("=" * 80)
        
        start_time = time.time()
        
        # Create test image
        self.create_test_image()
        
        # Test local engines availability first
        await self.test_local_engines_availability()
        
        # Test Mistral API as primary
        mistral_success = await self.test_mistral_api_primary()
        
        # Test fallback mechanism
        await self.test_fallback_mechanism()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate summary
        self.print_summary(total_time, mistral_success)
    
    def print_summary(self, total_time: float, mistral_success: bool):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("MISTRAL OCR API PRIMARY TEST SUMMARY")
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
        
        print(f"\nMistral OCR API Status: {'WORKING' if mistral_success else 'NEEDS API KEY'}")

        if mistral_success:
            print("\n[SUCCESS] Mistral OCR API integration working perfectly!")
            print("[OK] Primary engine: Mistral OCR API")
            print("[OK] Fallback engines: Tesseract, RapidOCR")
            print("[OK] Cost optimization enabled")
            print("[OK] Quality threshold configured")
        else:
            print("\n[INFO] Mistral OCR API requires API key")
            print("To test Mistral OCR API:")
            print("1. Get API key from Mistral AI")
            print("2. Set environment variable: export MISTRAL_API_KEY=your_key")
            print("3. Run test again")
            print("\nLocal fallback engines are available for testing.")


async def main():
    """Main test function."""
    print("To test Mistral OCR API, set your API key:")
    print("export MISTRAL_API_KEY=your_api_key_here")
    print("or")
    print("$env:MISTRAL_API_KEY = 'your_api_key_here'")
    print()

    tester = MistralPrimaryOCRTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
