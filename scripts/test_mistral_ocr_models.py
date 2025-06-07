#!/usr/bin/env python3
"""
Test Different Mistral OCR Models
Find which OCR models work with chat completions endpoint
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


async def test_ocr_models():
    """Test different OCR models with chat completions."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not found")
        return
    
    print(f"API Key: {api_key[:10]}...")
    print("=" * 80)
    
    # Create test image
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    draw.text((20, 50), "MISTRAL OCR MODEL TEST", fill='black', font=font)
    draw.text((20, 100), "Testing different OCR models.", fill='black', font=font)
    draw.text((20, 150), "Date: 2024-01-01", fill='black', font=font)
    
    # Convert to base64
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    image_b64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    # Models to test
    models_to_test = [
        "mistral-ocr-latest",
        "mistral-ocr-2505", 
        "mistral-ocr-2503",
        "pixtral-large-latest",
        "pixtral-large-2411",
        "pixtral-12b-latest",
        "mistral-large-pixtral-2411",
        "mistral-large-latest"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    working_models = []
    failed_models = []
    
    async with aiohttp.ClientSession() as session:
        for model in models_to_test:
            print(f"\nTesting model: {model}")
            print("-" * 40)
            
            payload = {
                "model": model,
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
                    
                    if response.status == 200:
                        result = await response.json()
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        usage = result.get("usage", {})
                        
                        print(f"[SUCCESS] {model}")
                        print(f"   Text extracted: {len(content)} characters")
                        print(f"   Tokens used: {usage.get('total_tokens', 0)}")
                        print(f"   Preview: {content[:100]}...")

                        working_models.append({
                            "model": model,
                            "text_length": len(content),
                            "tokens": usage.get('total_tokens', 0),
                            "content": content[:200]
                        })

                    else:
                        error_text = await response.text()
                        print(f"[FAILED] {model}")
                        print(f"   Status: {response.status}")
                        print(f"   Error: {error_text}")

                        failed_models.append({
                            "model": model,
                            "status": response.status,
                            "error": error_text[:200]
                        })

            except Exception as e:
                print(f"[ERROR] {model}")
                print(f"   Exception: {e}")
                failed_models.append({
                    "model": model,
                    "error": str(e)
                })
    
    # Summary
    print("\n" + "=" * 80)
    print("MISTRAL OCR MODEL TEST SUMMARY")
    print("=" * 80)
    
    print(f"\n[WORKING MODELS] ({len(working_models)}):")
    for model_info in working_models:
        print(f"  - {model_info['model']}")
        print(f"    Text: {model_info['text_length']} chars, Tokens: {model_info['tokens']}")

    print(f"\n[FAILED MODELS] ({len(failed_models)}):")
    for model_info in failed_models:
        print(f"  - {model_info['model']}")
        if 'status' in model_info:
            print(f"    Status: {model_info['status']}")
        print(f"    Error: {model_info['error'][:100]}...")

    if working_models:
        print(f"\n[RECOMMENDED MODEL] {working_models[0]['model']}")
        print("This model should be used in the configuration.")
    else:
        print("\n[NO WORKING OCR MODELS FOUND]")
        print("Check API access or model availability.")


if __name__ == "__main__":
    asyncio.run(test_ocr_models())
