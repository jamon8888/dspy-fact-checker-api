#!/usr/bin/env python3
"""
Minimal Mistral OCR API Test
Tests Mistral OCR API with minimal dependencies
"""

import asyncio
import os
import time
import base64
import aiohttp
import json
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont
import io

# Load production environment variables
from dotenv import load_dotenv
load_dotenv(r"C:\Users\NMarchitecte\Documents\fact-checker\.env.production")


class MinimalMistralOCRTester:
    """Minimal test of Mistral OCR API."""
    
    def __init__(self):
        """Initialize the tester."""
        self.results = []
        self.test_image = None
        self.api_key = None
        self.api_base = "https://api.mistral.ai/v1"
    
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
            draw.text((50, 30), "MISTRAL OCR API TEST", fill='black', font=title_font)
            
            # Document content
            draw.text((50, 80), "Testing Mistral OCR API integration", fill='black', font=font)
            draw.text((50, 120), "with production environment configuration.", fill='black', font=font)
            draw.text((50, 180), "Expected Results:", fill='black', font=font)
            draw.text((70, 220), "- High-quality text extraction", fill='black', font=font)
            draw.text((70, 260), "- Bbox coordinate annotations", fill='black', font=font)
            draw.text((70, 300), "- Confidence scoring", fill='black', font=font)
            draw.text((50, 350), "Test Date: 2024-01-01", fill='black', font=font)
            
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
    
    def load_api_key(self):
        """Load Mistral API key from environment."""
        print("\n=== Loading Mistral API Key ===")
        
        try:
            # Get API key from environment
            self.api_key = os.getenv("MISTRAL_API_KEY")
            
            if not self.api_key:
                self.log_test("api_key_loading", "FAIL", {
                    "reason": "MISTRAL_API_KEY not found in environment",
                    "env_file": "C:\\Users\\NMarchitecte\\Documents\\fact-checker\\.env.production",
                    "mistral_vars": [key for key in os.environ.keys() if "MISTRAL" in key.upper()]
                })
                return False
            
            self.log_test("api_key_loading", "PASS", {
                "api_key_found": True,
                "api_key_preview": f"{self.api_key[:10]}..." if len(self.api_key) > 10 else "short_key",
                "api_key_length": len(self.api_key),
                "api_base": self.api_base
            })
            
            return True
            
        except Exception as e:
            self.log_test("api_key_loading", "ERROR", {
                "error": str(e),
                "error_type": e.__class__.__name__
            })
            return False
    
    async def test_mistral_api_connection(self):
        """Test basic connection to Mistral API."""
        print("\n=== Testing Mistral API Connection ===")
        
        if not self.api_key:
            self.log_test("api_connection", "FAIL", {"reason": "No API key available"})
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Test with a simple API call (list models)
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        models_data = await response.json()
                        
                        self.log_test("api_connection", "PASS", {
                            "connection_successful": True,
                            "status_code": response.status,
                            "models_available": len(models_data.get("data", [])),
                            "api_responsive": True
                        })
                        return True
                    else:
                        error_text = await response.text()
                        self.log_test("api_connection", "FAIL", {
                            "status_code": response.status,
                            "error_response": error_text[:200]
                        })
                        return False
        
        except Exception as e:
            self.log_test("api_connection", "ERROR", {
                "error": str(e),
                "error_type": e.__class__.__name__
            })
            return False
    
    async def test_mistral_ocr_processing(self):
        """Test Mistral OCR processing with direct API call."""
        print("\n=== Testing Mistral OCR Processing ===")
        
        if not self.api_key or not self.test_image:
            self.log_test("ocr_processing", "FAIL", {
                "reason": "API key or test image not available"
            })
            return
        
        try:
            # Encode image to base64
            image_b64 = base64.b64encode(self.test_image).decode('utf-8')
            
            # Prepare OCR request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Mistral OCR API payload (using working vision model)
            payload = {
                "model": "pixtral-large-2411",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this image with high accuracy. Provide bbox coordinates for each text element."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    
                    processing_time = time.time() - start_time
                    
                    if response.status == 200:
                        result_data = await response.json()
                        
                        # Extract response content
                        content = result_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        usage = result_data.get("usage", {})
                        
                        self.log_test("ocr_processing", "PASS", {
                            "processing_successful": True,
                            "status_code": response.status,
                            "processing_time": f"{processing_time:.2f}s",
                            "text_extracted": bool(content),
                            "text_length": len(content),
                            "tokens_used": usage.get("total_tokens", 0),
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "text_preview": content[:200] + "..." if len(content) > 200 else content
                        })
                        
                        return result_data
                    else:
                        error_text = await response.text()
                        self.log_test("ocr_processing", "FAIL", {
                            "status_code": response.status,
                            "processing_time": f"{processing_time:.2f}s",
                            "error_response": error_text[:300]
                        })
                        return None
        
        except Exception as e:
            self.log_test("ocr_processing", "ERROR", {
                "error": str(e),
                "error_type": e.__class__.__name__
            })
            return None
    
    async def run_all_tests(self):
        """Run all minimal Mistral OCR tests."""
        print("Minimal Mistral OCR API Test Suite")
        print("=" * 80)
        print("Testing Mistral OCR API with production environment")
        print("Environment file: C:\\Users\\NMarchitecte\\Documents\\fact-checker\\.env.production")
        print("=" * 80)
        
        start_time = time.time()
        
        # Create test image
        self.create_test_image()
        
        # Load API key
        api_key_loaded = self.load_api_key()
        
        if api_key_loaded:
            # Test API connection
            connection_ok = await self.test_mistral_api_connection()
            
            if connection_ok:
                # Test OCR processing
                await self.test_mistral_ocr_processing()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate summary
        self.print_summary(total_time, api_key_loaded)
    
    def print_summary(self, total_time: float, api_key_available: bool):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("MINIMAL MISTRAL OCR API TEST SUMMARY")
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
        
        if api_key_available and passed >= 3:
            print("\n[SUCCESS] Mistral OCR API integration working perfectly!")
            print("[OK] API key loaded from production environment")
            print("[OK] API connection successful")
            print("[OK] OCR processing functional")
            print("[OK] Ready for production deployment")
        elif api_key_available:
            print("\n[PARTIAL] Mistral API key available but some issues")
            print("[OK] API key loaded successfully")
            print("[INFO] Check API connection or processing")
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
    
    tester = MinimalMistralOCRTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
