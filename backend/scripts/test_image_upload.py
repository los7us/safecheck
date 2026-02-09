"""
Manual test script for image upload feature.

Usage:
    python scripts/test_image_upload.py <path_to_test_image>
"""

import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.image_upload_handler import ImageUploadHandler
from src.services.gemini_service import GeminiService

load_dotenv()


async def test_image_upload(image_path: str):
    """Test uploading and analyzing an image"""
    print(f"\n📷 Testing image upload: {image_path}")
    print("=" * 60)
    
    # Read image file
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    print(f"   File size: {len(image_data) / 1024:.1f} KB")
    
    # Create handler
    upload_dir = Path("./uploads")
    handler = ImageUploadHandler(upload_dir=upload_dir)
    
    # Process upload
    print("\n📤 Processing upload...")
    post = await handler.process_upload(
        file_content=image_data,
        filename=Path(image_path).name,
        user_context="Test screenshot for analysis",
    )
    
    print(f"✓ Upload processed")
    print(f"  Post ID: {post.post_id}")
    print(f"  Text (first 200 chars): {post.post_text[:200]}...")
    
    if post.media_features:
        print(f"\n🖼️ Media Features:")
        print(f"  Caption: {post.media_features.caption}")
        if post.media_features.ocr_text:
            print(f"  OCR Text (first 200 chars): {post.media_features.ocr_text[:200]}...")
        else:
            print(f"  OCR Text: (none extracted)")
    
    # Analyze with Gemini
    print(f"\n🤖 Analyzing with Gemini...")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("⚠️  GEMINI_API_KEY not set, skipping analysis")
        return
    
    gemini = GeminiService(api_key=gemini_key)
    result = await gemini.analyze(post)
    
    print(f"\n📊 Analysis Result:")
    print(f"  Risk Score: {result.risk_score:.2f}")
    print(f"  Risk Level: {result.risk_level.value}")
    print(f"  Summary: {result.summary}")
    
    print(f"\n✅ Test completed successfully!")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_image_upload.py <path_to_image>")
        print("\nExample:")
        print("  python scripts/test_image_upload.py test_screenshot.png")
        return
    
    image_path = sys.argv[1]
    
    if not Path(image_path).exists():
        print(f"Error: File not found: {image_path}")
        return
    
    await test_image_upload(image_path)


if __name__ == "__main__":
    asyncio.run(main())
