#!/usr/bin/env python3
"""
Test Mistral API Models
Check available models and find the correct OCR model
"""

import asyncio
import os
import aiohttp
import json

# Load production environment variables
from dotenv import load_dotenv
load_dotenv(r"C:\Users\NMarchitecte\Documents\fact-checker\.env.production")


async def test_mistral_models():
    """Test available Mistral models."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not found")
        return
    
    print(f"API Key: {api_key[:10]}...")
    print("=" * 80)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.mistral.ai/v1/models",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    models_data = await response.json()
                    models = models_data.get("data", [])
                    
                    print(f"Found {len(models)} available models:")
                    print("=" * 80)
                    
                    # Look for vision/OCR models
                    vision_models = []
                    text_models = []
                    
                    for model in models:
                        model_id = model.get("id", "")
                        model_name = model.get("object", "")
                        
                        print(f"Model ID: {model_id}")
                        print(f"Object: {model_name}")
                        print(f"Created: {model.get('created', 'unknown')}")
                        print(f"Owned by: {model.get('owned_by', 'unknown')}")
                        
                        # Check if it's a vision model
                        if any(keyword in model_id.lower() for keyword in ['vision', 'ocr', 'pixtral', 'image']):
                            vision_models.append(model_id)
                            print("  *** VISION/OCR MODEL ***")
                        else:
                            text_models.append(model_id)
                        
                        print("-" * 40)
                    
                    print("\n" + "=" * 80)
                    print("VISION/OCR MODELS FOUND:")
                    print("=" * 80)
                    for model in vision_models:
                        print(f"  - {model}")
                    
                    print("\n" + "=" * 80)
                    print("TEXT MODELS:")
                    print("=" * 80)
                    for model in text_models[:10]:  # Show first 10
                        print(f"  - {model}")
                    
                    if len(text_models) > 10:
                        print(f"  ... and {len(text_models) - 10} more text models")
                    
                    # Test with a vision model if available
                    if vision_models:
                        print("\n" + "=" * 80)
                        print(f"TESTING OCR WITH: {vision_models[0]}")
                        print("=" * 80)
                        await test_ocr_with_model(session, headers, vision_models[0])
                    else:
                        print("\n" + "=" * 80)
                        print("NO VISION/OCR MODELS FOUND")
                        print("Trying with a general model that might support vision...")
                        print("=" * 80)
                        # Try with a general model that might support vision
                        general_models = [m for m in text_models if 'large' in m.lower() or 'latest' in m.lower()]
                        if general_models:
                            await test_ocr_with_model(session, headers, general_models[0])
                
                else:
                    error_text = await response.text()
                    print(f"ERROR: Status {response.status}")
                    print(f"Response: {error_text}")
    
    except Exception as e:
        print(f"ERROR: {e}")


async def test_ocr_with_model(session, headers, model_id):
    """Test OCR with a specific model."""
    
    # Create a simple test image (base64 encoded)
    import base64
    from PIL import Image, ImageDraw, ImageFont
    import io
    
    # Create test image
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    draw.text((20, 50), "MISTRAL OCR TEST", fill='black', font=font)
    draw.text((20, 100), "This is a test document for OCR.", fill='black', font=font)
    draw.text((20, 150), "Date: 2024-01-01", fill='black', font=font)
    
    # Convert to base64
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    image_b64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    # Test OCR request
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all text from this image."
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
        "max_tokens": 500,
        "temperature": 0.1
    }
    
    try:
        async with session.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as response:
            
            print(f"OCR Test Status: {response.status}")
            
            if response.status == 200:
                result = await response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = result.get("usage", {})
                
                print("SUCCESS! OCR Response:")
                print(f"Extracted Text: {content}")
                print(f"Tokens Used: {usage.get('total_tokens', 0)}")
                print(f"Model: {model_id}")
                
                return True
            else:
                error_text = await response.text()
                print(f"FAILED: {error_text}")
                return False
    
    except Exception as e:
        print(f"ERROR during OCR test: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_mistral_models())
