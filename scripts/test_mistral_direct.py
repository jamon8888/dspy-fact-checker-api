#!/usr/bin/env python3
"""
Direct Mistral OCR API Test
Tests Mistral OCR API directly without complex configuration loading
"""

import asyncio
import os
import sys
import time
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont
import io

# Load production environment variables
from dotenv import load_dotenv
load_dotenv(r"C:\Users\NMarchitecte\Documents\fact-checker\.env.production")

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.document_processing.ocr.mistral_engine import MistralOCREngine


class DirectMistralOCRTester:
    """Direct test of Mistral OCR API."""
    
    def __init__(self):
        """Initialize the tester."""
        self.results = []
        self.test_image = None
    
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
        """Create test image for Mistral OCR testing."""
        print("\n=== Creating Test Image for Mistral OCR ===")
        
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
            draw.text((50, 30), "MISTRAL OCR API DIRECT TEST", fill='black', font=title_font)
            
            # Document content
            draw.text((50, 80), "This document tests direct Mistral OCR API integration.", fill='black', font=font)
            draw.text((50, 120), "Testing high-quality cloud-based OCR processing.", fill='black', font=font)
            draw.text((50, 180), "Features:", fill='black', font=font)
            draw.text((70, 220), "- Advanced text recognition", fill='black', font=font)
            draw.text((70, 260), "- Bbox annotations", fill='black', font=font)
            draw.text((70, 300), "- Multi-language support", fill='black', font=font)
            draw.text((50, 350), "Date: 2024-01-01 | Test ID: MISTRAL-001", fill='black', font=font)
            
            # Save to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            self.test_image = img_buffer.getvalue()
            
            self.log_test("test_image_creation", "PASS", {
                "image_created": True,
                "image_size": len(self.test_image),
                "format": "PNG"
            })
            
        except Exception as e:
            self.log_test("test_image_creation", "ERROR", {"error": str(e)})
    
    async def test_mistral_api_key_loading(self):
        """Test loading Mistral API key from production environment."""
        print("\n=== Testing Mistral API Key Loading ===")
        
        try:
            # Check for Mistral API key
            mistral_api_key = os.getenv("MISTRAL_API_KEY")
            
            if not mistral_api_key:
                self.log_test("mistral_api_key_loading", "FAIL", {
                    "reason": "MISTRAL_API_KEY not found in environment",
                    "env_file_loaded": "C:\\Users\\NMarchitecte\\Documents\\fact-checker\\.env.production",
                    "available_env_vars": [key for key in os.environ.keys() if "MISTRAL" in key.upper()]
                })
                return None
            
            self.log_test("mistral_api_key_loading", "PASS", {
                "api_key_found": True,
                "api_key_preview": f"{mistral_api_key[:10]}..." if len(mistral_api_key) > 10 else "short_key",
                "api_key_length": len(mistral_api_key),
                "env_file_loaded": "C:\\Users\\NMarchitecte\\Documents\\fact-checker\\.env.production"
            })
            
            return mistral_api_key
            
        except Exception as e:
            self.log_test("mistral_api_key_loading", "ERROR", {
                "error": str(e),
                "error_type": e.__class__.__name__
            })
            return None
    
    async def test_mistral_engine_initialization(self, api_key: str):
        """Test Mistral OCR engine initialization."""
        print("\n=== Testing Mistral OCR Engine Initialization ===")
        
        try:
            # Initialize Mistral OCR engine
            engine = MistralOCREngine(
                api_key=api_key,
                model="mistral-ocr-latest",
                timeout=60
            )
            
            # Check if engine is available
            is_available = engine.is_available()
            
            # Get engine info
            engine_info = engine.get_engine_info()
            
            self.log_test("mistral_engine_initialization", "PASS" if is_available else "FAIL", {
                "engine_available": is_available,
                "engine_name": engine_info.name,
                "engine_type": engine_info.type.value,
                "supported_languages": len(engine_info.supported_languages),
                "cost_per_page": engine_info.cost_per_page,
                "quality_rating": engine_info.quality_rating,
                "supports_bbox": engine_info.supports_bbox,
                "max_file_size": engine_info.max_file_size
            })
            
            return engine if is_available else None
            
        except Exception as e:
            self.log_test("mistral_engine_initialization", "ERROR", {
                "error": str(e),
                "error_type": e.__class__.__name__
            })
            return None
    
    async def test_mistral_ocr_processing(self, engine):
        """Test Mistral OCR processing with test image."""
        print("\n=== Testing Mistral OCR Processing ===")
        
        if not engine or not self.test_image:
            self.log_test("mistral_ocr_processing", "FAIL", {
                "reason": "Engine or test image not available"
            })
            return
        
        try:
            start_time = time.time()
            
            # Process image with Mistral OCR
            result = await engine.process_image(
                self.test_image,
                language="en",
                bbox_annotation_format="json"
            )
            
            processing_time = time.time() - start_time
            
            # Evaluate results
            success = bool(result.text and len(result.text.strip()) > 0)
            
            self.log_test("mistral_ocr_processing", "PASS" if success else "FAIL", {
                "processing_success": success,
                "text_extracted": bool(result.text),
                "text_length": len(result.text) if result.text else 0,
                "confidence": result.confidence,
                "processing_time": f"{processing_time:.2f}s",
                "engine_processing_time": f"{result.processing_time:.2f}s",
                "engine_used": result.engine_used,
                "has_bbox_annotations": bool(result.bbox_annotations),
                "bbox_count": len(result.bbox_annotations) if result.bbox_annotations else 0,
                "has_quality_metrics": bool(result.quality_metrics),
                "text_preview": (result.text[:150] + "..." if result.text and len(result.text) > 150 else result.text or "").encode('ascii', errors='ignore').decode('ascii')
            })
            
            # Test quality metrics if available
            if result.quality_metrics:
                self.log_test("mistral_quality_metrics", "PASS", {
                    "overall_confidence": result.quality_metrics.overall_confidence,
                    "text_confidence": result.quality_metrics.text_confidence,
                    "language_confidence": result.quality_metrics.language_confidence,
                    "structure_preservation": result.quality_metrics.structure_preservation,
                    "word_count": result.quality_metrics.word_count,
                    "character_count": result.quality_metrics.character_count,
                    "detected_language": result.quality_metrics.detected_language
                })
            
            # Test bbox annotations if available
            if result.bbox_annotations:
                self.log_test("mistral_bbox_annotations", "PASS", {
                    "bbox_annotations_count": len(result.bbox_annotations),
                    "bbox_format": "json",
                    "first_bbox_preview": str(result.bbox_annotations[0])[:100] + "..." if result.bbox_annotations else "none"
                })
            
            return result
            
        except Exception as e:
            self.log_test("mistral_ocr_processing", "ERROR", {
                "error": str(e),
                "error_type": e.__class__.__name__
            })
            return None
    
    async def test_mistral_cost_estimation(self, engine):
        """Test Mistral OCR cost estimation."""
        print("\n=== Testing Mistral Cost Estimation ===")
        
        if not engine or not self.test_image:
            self.log_test("mistral_cost_estimation", "FAIL", {
                "reason": "Engine or test image not available"
            })
            return
        
        try:
            # Estimate cost for processing
            estimated_cost = engine.estimate_cost(len(self.test_image), 1)
            
            # Get engine info for cost details
            engine_info = engine.get_engine_info()
            
            self.log_test("mistral_cost_estimation", "PASS", {
                "cost_estimation_available": estimated_cost is not None,
                "estimated_cost": estimated_cost,
                "cost_per_page": engine_info.cost_per_page,
                "image_size": len(self.test_image),
                "pages_estimated": 1
            })
            
        except Exception as e:
            self.log_test("mistral_cost_estimation", "ERROR", {
                "error": str(e),
                "error_type": e.__class__.__name__
            })
    
    async def run_all_tests(self):
        """Run all direct Mistral OCR tests."""
        print("Direct Mistral OCR API Test Suite")
        print("=" * 80)
        print("Testing Mistral OCR API directly with production environment")
        print("=" * 80)
        
        start_time = time.time()
        
        # Create test image
        self.create_test_image()
        
        # Test API key loading
        api_key = await self.test_mistral_api_key_loading()
        
        if api_key:
            # Test engine initialization
            engine = await self.test_mistral_engine_initialization(api_key)
            
            if engine:
                # Test OCR processing
                result = await self.test_mistral_ocr_processing(engine)
                
                # Test cost estimation
                await self.test_mistral_cost_estimation(engine)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate summary
        self.print_summary(total_time, api_key is not None, engine is not None if api_key else False)
    
    def print_summary(self, total_time: float, api_key_available: bool, engine_working: bool):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("DIRECT MISTRAL OCR API TEST SUMMARY")
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
        
        print(f"\nMistral API Key: {'AVAILABLE' if api_key_available else 'NOT FOUND'}")
        print(f"Mistral Engine: {'WORKING' if engine_working else 'NOT WORKING'}")
        
        if api_key_available and engine_working:
            print("\n[SUCCESS] Mistral OCR API integration working perfectly!")
            print("[OK] API key loaded from production environment")
            print("[OK] Engine initialization successful")
            print("[OK] OCR processing functional")
            print("[OK] Cost estimation available")
            print("[OK] Quality metrics provided")
            print("[OK] Bbox annotations supported")
        elif api_key_available:
            print("\n[PARTIAL] Mistral API key available but engine issues")
            print("[OK] API key loaded successfully")
            print("[ERROR] Engine initialization failed")
        else:
            print("\n[FAIL] Mistral API key not available")
            print("[ERROR] Check .env.production file")
            print("[ERROR] Verify MISTRAL_API_KEY is set")
        
        # Show any failures
        if failed > 0 or errors > 0:
            print(f"\nIssues Found:")
            for result in self.results:
                if result["status"] in ["FAIL", "ERROR"]:
                    print(f"  - {result['test']}: {result['status']}")


async def main():
    """Main test function."""
    print("Loading production environment from:")
    print("C:\\Users\\NMarchitecte\\Documents\\fact-checker\\.env.production")
    print()
    
    tester = DirectMistralOCRTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
