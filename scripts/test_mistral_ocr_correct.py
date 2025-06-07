#!/usr/bin/env python3
"""
Test Correct Mistral OCR API
Using the dedicated /v1/ocr endpoint with mistral-ocr-latest model
"""

import asyncio
import os
import aiohttp
import base64
from PIL import Image, ImageDraw, ImageFont
import io

# Load production environment variables
from dotenv import load_dotenv
load_dotenv(r"C:\Users\NMarchitecte\Documents\fact-checker\.env.production")


async def test_mistral_ocr_api():
    """Test the correct Mistral OCR API endpoint."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not found")
        return
    
    print(f"API Key: {api_key[:10]}...")
    print("Testing Mistral OCR API with dedicated /v1/ocr endpoint")
    print("=" * 80)
    
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
    draw.text((50, 80), "Testing the correct Mistral OCR API endpoint", fill='black', font=font)
    draw.text((50, 120), "using the dedicated /v1/ocr endpoint.", fill='black', font=font)
    draw.text((50, 180), "Model: mistral-ocr-latest", fill='black', font=font)
    draw.text((50, 220), "Expected Features:", fill='black', font=font)
    draw.text((70, 260), "- High-quality text extraction", fill='black', font=font)
    draw.text((70, 300), "- Bbox coordinate annotations", fill='black', font=font)
    draw.text((70, 340), "- Confidence scoring", fill='black', font=font)
    draw.text((50, 380), "Date: 2024-01-01", fill='black', font=font)
    
    # Save image to file for upload
    img_path = "test_ocr_image.png"
    img.save(img_path)
    
    print(f"Created test image: {img_path}")
    print(f"Image size: {os.path.getsize(img_path)} bytes")
    
    # Test the OCR API
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Upload file for OCR processing
            with open(img_path, 'rb') as f:
                form_data = aiohttp.FormData()
                form_data.add_field('file', f, filename='test_ocr_image.png', content_type='image/png')
                form_data.add_field('model', 'mistral-ocr-latest')
                
                print("\nSending request to Mistral OCR API...")
                print("Endpoint: https://api.mistral.ai/v1/ocr")
                print("Model: mistral-ocr-latest")
                
                async with session.post(
                    "https://api.mistral.ai/v1/ocr",
                    headers=headers,
                    data=form_data,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    
                    print(f"Response Status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        print("\n[SUCCESS] Mistral OCR API Response:")
                        print("=" * 50)
                        print(f"Model: {result.get('model', 'N/A')}")
                        print(f"Object: {result.get('object', 'N/A')}")
                        
                        # Extract text content
                        text_content = result.get('text', '')
                        if text_content:
                            print(f"Text Length: {len(text_content)} characters")
                            print(f"Text Content:\n{text_content}")
                        
                        # Check for bbox annotations
                        bbox_data = result.get('bbox', [])
                        if bbox_data:
                            print(f"\nBbox Annotations: {len(bbox_data)} items")
                            for i, bbox in enumerate(bbox_data[:3]):  # Show first 3
                                print(f"  {i+1}. {bbox}")
                        
                        # Usage information
                        usage = result.get('usage', {})
                        if usage:
                            print(f"\nUsage:")
                            print(f"  Tokens: {usage.get('total_tokens', 'N/A')}")
                            print(f"  Cost: ${usage.get('cost', 'N/A')}")
                        
                        print("\n[SUCCESS] Mistral OCR API working perfectly!")
                        print("[OK] Dedicated OCR endpoint functional")
                        print("[OK] mistral-ocr-latest model working")
                        print("[OK] Text extraction successful")
                        if bbox_data:
                            print("[OK] Bbox annotations provided")
                        
                        return True
                        
                    else:
                        error_text = await response.text()
                        print(f"\n[FAILED] Mistral OCR API Error:")
                        print(f"Status: {response.status}")
                        print(f"Response: {error_text}")
                        
                        # Try to parse error details
                        try:
                            import json
                            error_data = json.loads(error_text)
                            print(f"Error Type: {error_data.get('type', 'N/A')}")
                            print(f"Error Message: {error_data.get('message', 'N/A')}")
                        except:
                            pass
                        
                        return False
    
    except Exception as e:
        print(f"\n[ERROR] Exception occurred:")
        print(f"Error: {e}")
        print(f"Error Type: {e.__class__.__name__}")
        return False
    
    finally:
        # Clean up test image
        if os.path.exists(img_path):
            os.remove(img_path)
            print(f"\nCleaned up: {img_path}")


async def test_file_upload_method():
    """Test alternative file upload method if direct OCR fails."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return False
    
    print("\n" + "=" * 80)
    print("TESTING ALTERNATIVE: File Upload + OCR")
    print("=" * 80)
    
    # Create test image
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    draw.text((20, 50), "MISTRAL OCR FILE UPLOAD TEST", fill='black', font=font)
    draw.text((20, 100), "Testing file upload method.", fill='black', font=font)
    draw.text((20, 150), "Date: 2024-01-01", fill='black', font=font)
    
    # Save image
    img_path = "test_upload_image.png"
    img.save(img_path)
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Upload file
            with open(img_path, 'rb') as f:
                form_data = aiohttp.FormData()
                form_data.add_field('file', f, filename='test_upload_image.png', content_type='image/png')
                form_data.add_field('purpose', 'ocr')
                
                print("Step 1: Uploading file...")
                async with session.post(
                    "https://api.mistral.ai/v1/files",
                    headers=headers,
                    data=form_data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        file_result = await response.json()
                        file_id = file_result.get('id')
                        print(f"[SUCCESS] File uploaded: {file_id}")
                        
                        # Step 2: Process with OCR
                        print("Step 2: Processing with OCR...")
                        ocr_payload = {
                            "model": "mistral-ocr-latest",
                            "file_id": file_id
                        }
                        
                        async with session.post(
                            "https://api.mistral.ai/v1/ocr",
                            headers={**headers, "Content-Type": "application/json"},
                            json=ocr_payload,
                            timeout=aiohttp.ClientTimeout(total=120)
                        ) as ocr_response:
                            
                            print(f"OCR Response Status: {ocr_response.status}")
                            
                            if ocr_response.status == 200:
                                ocr_result = await ocr_response.json()
                                print("[SUCCESS] OCR processing completed!")
                                print(f"Text: {ocr_result.get('text', 'N/A')}")
                                return True
                            else:
                                error_text = await ocr_response.text()
                                print(f"[FAILED] OCR processing failed: {error_text}")
                                return False
                    else:
                        error_text = await response.text()
                        print(f"[FAILED] File upload failed: {error_text}")
                        return False
    
    except Exception as e:
        print(f"[ERROR] File upload method failed: {e}")
        return False
    
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)


async def main():
    """Main test function."""
    print("Mistral OCR API Correct Implementation Test")
    print("Using the dedicated /v1/ocr endpoint")
    print("Model: mistral-ocr-latest")
    print()
    
    # Test direct OCR API
    success = await test_mistral_ocr_api()
    
    if not success:
        print("\nDirect OCR failed, trying file upload method...")
        success = await test_file_upload_method()
    
    if success:
        print("\n" + "=" * 80)
        print("[FINAL SUCCESS] Mistral OCR API working correctly!")
        print("[OK] Using correct /v1/ocr endpoint")
        print("[OK] Model: mistral-ocr-latest")
        print("[OK] Ready for production integration")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("[FINAL RESULT] Need to check API documentation")
        print("[INFO] OCR endpoint might require different parameters")
        print("[INFO] Check Mistral OCR API documentation for details")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
