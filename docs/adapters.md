# Platform Adapter Guide

## Overview

Platform adapters extract content from platform-specific URLs and normalize to the `CanonicalPost` schema.

## Implemented Adapters

### Reddit (`RedditAdapter`)

**Config:**
```python
config = {
    "client_id": "your_reddit_client_id",
    "client_secret": "your_reddit_client_secret",
    "user_agent": "SafetyCheck/1.0",
}
```

**URL Format:** `https://reddit.com/r/subreddit/comments/post_id/...`

**Extracts:**
- Post title + selftext
- Author metadata (account age bucket, karma bucket)
- Engagement (upvotes, comments)
- Media (images, galleries, videos)
- Top 5 comments
- External links

---

### Twitter/X (`TwitterAdapter`)

**Config:**
```python
config = {
    "bearer_token": "optional_twitter_bearer",  # Falls back to nitter
    "nitter_instance": "https://nitter.net",
}
```

**URL Format:** 
- `https://twitter.com/username/status/tweet_id`
- `https://x.com/username/status/tweet_id`

**Extracts:**
- Tweet text
- Author metadata (if API available)
- Engagement (likes, retweets, replies)
- Media (images, videos)
- External links

---

## Adapter Interface

All adapters implement `PlatformAdapter`:

```python
class PlatformAdapter(ABC):
    @property
    def platform_name(self) -> PlatformName: ...
    
    @property
    def url_pattern(self) -> re.Pattern: ...
    
    async def extract(self, url: str) -> CanonicalPost: ...
    
    async def extract_from_text(self, text: str, context=None) -> CanonicalPost: ...
```

---

## Testing

```bash
# Unit tests
pytest tests/unit/test_reddit_adapter.py -v
pytest tests/unit/test_twitter_adapter.py -v

# Validation script
python scripts/validate_adapters.py
```

---

## Adding New Adapters

1. Create `src/adapters/your_platform_adapter.py`
2. Implement `PlatformAdapter` interface
3. Add to `src/adapters/__init__.py`
4. Register in `adapter_registry`
5. Add tests
