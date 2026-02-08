# Media Pipeline Documentation

## Overview

The media pipeline handles downloading, caching, and feature extraction from images in social media posts.

## Architecture

```
URL → Adapter → CanonicalPost (media URLs)
                    ↓
              MediaProcessor
                    ↓
          ┌────────┴────────┐
          ↓                 ↓
     MediaCache      ImageFeatureExtractor
     (Download)      (Caption, OCR)
          ↓                 ↓
     Cached File     MediaFeatures
                           ↓
               CanonicalPost (enriched)
```

## Components

### MediaCache
Content-addressed cache using SHA-256 hashing.

```python
from src.utils.media_cache import MediaCache

cache = MediaCache(Path("./media_cache"), max_size_mb=10)
file_path, content_hash = await cache.download_and_cache(url)
```

### ImageFeatureExtractor
Extracts caption and OCR text from images.

```python
from src.services.image_features import ImageFeatureExtractor

extractor = ImageFeatureExtractor()
features = await extractor.extract_features(image_path)
# features.caption, features.ocr_text
```

### MediaProcessor
Orchestrates downloading and feature extraction.

```python
from src.services.media_processor import MediaProcessor

processor = MediaProcessor(cache_dir=Path("./media_cache"))
metadata, features = await processor.process_media(url, MediaType.IMAGE)
```

---

## Why Extract Features Instead of Sending Images?

| Approach | Cost | Latency |
|----------|------|---------|
| Send images to Gemini | High | High |
| **Extract text features** | **Low** | **Low** |

We extract text descriptions and send those to Gemini for reasoning.

---

## OCR Setup

OCR requires Tesseract installed:

**Windows:** Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)

**macOS:** `brew install tesseract`

**Ubuntu:** `sudo apt-get install tesseract-ocr`

---

## Testing

```bash
# Unit tests
pytest tests/unit/test_media_cache.py -v

# Manual test
python scripts/test_media_pipeline.py https://example.com/image.jpg
```
