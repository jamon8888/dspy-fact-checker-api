#!/usr/bin/env python3
"""
Simple Mistral OCR Test
Tests Mistral OCR API with a simple example
"""

import asyncio
import os
import sys
import base64
from PIL import Image, ImageDraw, ImageFont
import io

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.document_processing.ocr.mistral_engine import MistralOCREngine


async def test_mistral_ocr():
    """Test Mistral OCR with a simple image."""
    
    print("=== Mistral OCR Simple Test ===")
    
    # Check for API key
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ MISTRAL_API_KEY environment variable not set")
        print("Please set your Mistral API key:")
        print("export MISTRAL_API_KEY=your_api_key_here")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        # Create Mistral OCR engine
        print("🔧 Initializing Mistral OCR engine...")
        engine = MistralOCREngine(api_key=api_key)
        
        if not engine.is_available():
            print("❌ Mistral OCR engine not available")
            return
        
        print("✅ Mistral OCR engine initialized successfully")
        
        # Create a simple test image
        print("🖼️ Creating test image...")
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((20, 50), "Hello Mistral OCR!", fill='black', font=font)
        draw.text((20, 100), "This is a test document.", fill='black', font=font)
        draw.text((20, 150), "Date: 2024-01-01", fill='black', font=font)
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        image_data = img_buffer.getvalue()
        
        print(f"✅ Test image created ({len(image_data)} bytes)")
        
        # Process with Mistral OCR
        print("🚀 Processing image with Mistral OCR...")
        result = await engine.process_image(image_data, language="en")
        
        print("✅ OCR processing completed!")
        print(f"📝 Extracted text: {result.text}")
        print(f"🎯 Confidence: {result.confidence:.2f}")
        print(f"⏱️ Processing time: {result.processing_time:.2f}s")
        print(f"🔧 Engine used: {result.engine_used}")
        
        if result.bbox_annotations:
            print(f"📍 Bbox annotations: {len(result.bbox_annotations)} found")
        
        if result.quality_metrics:
            print(f"📊 Quality metrics:")
            print(f"   - Overall confidence: {result.quality_metrics.overall_confidence:.2f}")
            print(f"   - Word count: {result.quality_metrics.word_count}")
            print(f"   - Character count: {result.quality_metrics.character_count}")
        
        # Test engine info
        engine_info = engine.get_engine_info()
        print(f"ℹ️ Engine info:")
        print(f"   - Name: {engine_info.name}")
        print(f"   - Type: {engine_info.type.value}")
        print(f"   - Supported languages: {len(engine_info.supported_languages)}")
        print(f"   - Cost per page: ${engine_info.cost_per_page}")
        print(f"   - Quality rating: {engine_info.quality_rating}")
        
        print("\n🎉 Mistral OCR test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {e.__class__.__name__}")


async def main():
    """Main function."""
    await test_mistral_ocr()


if __name__ == "__main__":
    asyncio.run(main())
