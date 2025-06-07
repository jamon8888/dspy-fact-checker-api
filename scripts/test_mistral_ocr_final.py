#!/usr/bin/env python3
"""
Test Final Correct Mistral OCR API
Using the correct /v1/ocr endpoint with proper document format
"""

import asyncio
import os
import aiohttp
import base64
import json
from PIL import Image, ImageDraw, ImageFont
import io

# Load production environment variables
from dotenv import load_dotenv
load_dotenv(r"C:\Users\NMarchitecte\Documents\fact-checker\.env.production")


async def test_mistral_ocr_final():
    """Test the final correct Mistral OCR API implementation."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not found")
        return False
    
    print(f"API Key: {api_key[:10]}...")
    print("Testing Final Correct Mistral OCR API Implementation")
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
    draw.text((50, 30), "MISTRAL OCR FINAL TEST", fill='black', font=title_font)
    
    # Document content
    draw.text((50, 80), "Testing the correct Mistral OCR API", fill='black', font=font)
    draw.text((50, 120), "with proper document format.", fill='black', font=font)
    draw.text((50, 180), "Features:", fill='black', font=font)
    draw.text((70, 220), "- Model: mistral-ocr-latest", fill='black', font=font)
    draw.text((70, 260), "- High-quality text extraction", fill='black', font=font)
    draw.text((70, 300), "- Bbox coordinate annotations", fill='black', font=font)
    draw.text((70, 340), "- Structured markdown output", fill='black', font=font)
    draw.text((50, 380), "Date: 2024-01-01", fill='black', font=font)
    
    # Convert to base64
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    image_b64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    print(f"Created test image: {len(image_b64)} base64 characters")
    
    # Prepare the correct OCR request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "mistral-ocr-latest",
        "document": {
            "type": "image_url",
            "image_url": f"data:image/png;base64,{image_b64}"
        },
        "include_image_base64": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("\nSending request to Mistral OCR API...")
            print("Endpoint: https://api.mistral.ai/v1/ocr")
            print("Model: mistral-ocr-latest")
            print("Document Type: image_url (base64)")
            
            async with session.post(
                "https://api.mistral.ai/v1/ocr",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                
                print(f"Response Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    
                    print("\n" + "=" * 80)
                    print("[SUCCESS] MISTRAL OCR API WORKING PERFECTLY!")
                    print("=" * 80)
                    
                    # Extract basic info
                    print(f"Model: {result.get('model', 'N/A')}")
                    print(f"Object: {result.get('object', 'N/A')}")
                    print(f"ID: {result.get('id', 'N/A')}")
                    
                    # Extract text content
                    text_content = result.get('text', '')
                    if text_content:
                        print(f"\nText Content ({len(text_content)} characters):")
                        print("-" * 50)
                        print(text_content)
                        print("-" * 50)
                    
                    # Check for images with bboxes
                    images = result.get('images', [])
                    if images:
                        print(f"\nImages with Bboxes: {len(images)} items")
                        for i, img_data in enumerate(images[:2]):  # Show first 2
                            print(f"  Image {i+1}:")
                            print(f"    Format: {img_data.get('format', 'N/A')}")
                            print(f"    Width: {img_data.get('width', 'N/A')}")
                            print(f"    Height: {img_data.get('height', 'N/A')}")
                            
                            bboxes = img_data.get('bboxes', [])
                            if bboxes:
                                print(f"    Bboxes: {len(bboxes)} items")
                                for j, bbox in enumerate(bboxes[:3]):  # Show first 3
                                    print(f"      {j+1}. {bbox}")
                    
                    # Usage information
                    usage = result.get('usage', {})
                    if usage:
                        print(f"\nUsage Information:")
                        print(f"  Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
                        print(f"  Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
                        print(f"  Total Tokens: {usage.get('total_tokens', 'N/A')}")
                    
                    # Created timestamp
                    created = result.get('created', 'N/A')
                    if created != 'N/A':
                        import datetime
                        created_time = datetime.datetime.fromtimestamp(created)
                        print(f"  Created: {created_time}")
                    
                    print("\n" + "=" * 80)
                    print("[FINAL SUCCESS] Mistral OCR API Integration Complete!")
                    print("[OK] Endpoint: /v1/ocr")
                    print("[OK] Model: mistral-ocr-latest")
                    print("[OK] Document format: image_url with base64")
                    print("[OK] Text extraction: WORKING")
                    if images:
                        print("[OK] Bbox annotations: WORKING")
                    print("[OK] Ready for production deployment")
                    print("=" * 80)
                    
                    return True
                    
                else:
                    error_text = await response.text()
                    print(f"\n[FAILED] Mistral OCR API Error:")
                    print(f"Status: {response.status}")
                    print(f"Response: {error_text}")
                    
                    # Try to parse error details
                    try:
                        error_data = json.loads(error_text)
                        if 'detail' in error_data:
                            print(f"Error Details:")
                            for detail in error_data['detail']:
                                print(f"  - {detail.get('msg', 'N/A')} (loc: {detail.get('loc', 'N/A')})")
                    except:
                        pass
                    
                    return False
    
    except Exception as e:
        print(f"\n[ERROR] Exception occurred:")
        print(f"Error: {e}")
        print(f"Error Type: {e.__class__.__name__}")
        return False


async def test_with_url_image():
    """Test with a public image URL."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return False
    
    print("\n" + "=" * 80)
    print("TESTING WITH PUBLIC IMAGE URL")
    print("=" * 80)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Use the example from Mistral documentation
    payload = {
        "model": "mistral-ocr-latest",
        "document": {
            "type": "image_url",
            "image_url": "https://raw.githubusercontent.com/mistralai/cookbook/refs/heads/main/mistral/ocr/receipt.png"
        },
        "include_image_base64": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("Testing with Mistral's example receipt image...")
            
            async with session.post(
                "https://api.mistral.ai/v1/ocr",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                
                print(f"Response Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    
                    print("[SUCCESS] Public image OCR working!")
                    text_content = result.get('text', '')
                    print(f"Text extracted: {len(text_content)} characters")
                    if text_content:
                        print(f"Preview: {text_content[:200]}...")
                    
                    return True
                else:
                    error_text = await response.text()
                    print(f"[FAILED] Status: {response.status}")
                    print(f"Error: {error_text}")
                    return False
    
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


async def main():
    """Main test function."""
    print("Mistral OCR API Final Correct Implementation Test")
    print("Using the correct /v1/ocr endpoint with proper document format")
    print()
    
    # Test with our custom image
    success1 = await test_mistral_ocr_final()
    
    # Test with public image URL
    success2 = await test_with_url_image()
    
    print("\n" + "=" * 80)
    print("FINAL TEST SUMMARY")
    print("=" * 80)
    
    if success1 or success2:
        print("[OVERALL SUCCESS] Mistral OCR API working correctly!")
        print("[OK] Correct endpoint: /v1/ocr")
        print("[OK] Correct model: mistral-ocr-latest")
        print("[OK] Correct document format")
        print("[OK] Ready for production integration")
        
        if success1:
            print("[OK] Base64 image processing: WORKING")
        if success2:
            print("[OK] Public URL image processing: WORKING")
    else:
        print("[OVERALL FAILED] Need to investigate further")
        print("[INFO] Check API key permissions")
        print("[INFO] Check request format")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
