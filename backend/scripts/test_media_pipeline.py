"""
Manual test script for media pipeline.

Usage:
    python scripts/test_media_pipeline.py [image_url]
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.media_processor import MediaProcessor
from src.core.schemas import MediaType


async def test_image(url: str):
    """Test processing a single image"""
    print(f"\nProcessing image: {url}")
    print("=" * 60)
    
    # Create processor
    cache_dir = Path("./media_cache")
    processor = MediaProcessor(cache_dir)
    
    try:
        # Process image
        metadata, features = await processor.process_media(url, MediaType.IMAGE)
        
        # Display results
        print("\n📊 METADATA:")
        print(f"  Hash: {metadata.hash[:16]}...")
        if metadata.width and metadata.height:
            print(f"  Size: {metadata.width}x{metadata.height}")
        if metadata.size_bytes:
            print(f"  File size: {metadata.size_bytes / 1024:.1f} KB")
        
        print("\n🔍 FEATURES:")
        print(f"  Caption: {features.caption}")
        if features.ocr_text:
            print(f"\n  OCR Text:")
            print(f"  {'-' * 50}")
            ocr_preview = features.ocr_text[:500] + "..." if len(features.ocr_text) > 500 else features.ocr_text
            print(f"  {ocr_preview}")
            print(f"  {'-' * 50}")
        else:
            print(f"  OCR Text: (none detected)")
        
        # Show cache stats
        print("\n💾 CACHE STATS:")
        metrics = processor.get_metrics()
        cache_stats = metrics['cache_stats']
        print(f"  Total files: {cache_stats['total_files']}")
        print(f"  Total size: {cache_stats['total_size_mb']:.2f} MB")
        
        print("\n✅ Success!")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await processor.cleanup()


async def test_sample_images():
    """Test with sample images"""
    print("\n🔍 Testing sample images...")
    
    test_images = [
        "https://via.placeholder.com/400x300.png/09f/fff?text=Test+Image",
        "https://via.placeholder.com/600x400.png/0f0/000?text=Sample",
    ]
    
    cache_dir = Path("./media_cache")
    processor = MediaProcessor(cache_dir)
    
    for url in test_images:
        print(f"\nTesting: {url[:60]}...")
        try:
            metadata, features = await processor.process_media(url, MediaType.IMAGE)
            print(f"  ✓ Hash: {metadata.hash[:16]}...")
            print(f"  ✓ Caption: {features.caption}")
            if features.ocr_text:
                print(f"  ✓ OCR found: {len(features.ocr_text)} chars")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    await processor.cleanup()
    print("\n✅ Sample tests complete!")


async def main():
    """Main entry point"""
    print("SafetyCheck Media Pipeline Test")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # Test specific URL
        url = sys.argv[1]
        await test_image(url)
    else:
        # Run standard tests
        await test_sample_images()


if __name__ == "__main__":
    asyncio.run(main())
