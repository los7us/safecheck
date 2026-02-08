"""
Twitter/X Platform Adapter

Extracts content from Twitter/X posts and normalizes to CanonicalPost schema.

Implementation Strategy:
- Primary: Twitter API v2 (if bearer token available)
- Fallback: Public scraping via nitter instances
- Paste mode: Always available

Supported URL formats:
- https://twitter.com/username/status/tweet_id
- https://x.com/username/status/tweet_id
"""

import re
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx

from src.adapters.base_adapter import (
    PlatformAdapter,
    URLParseError,
    ContentExtractionError,
    RateLimitError,
)
from src.core.schemas import (
    CanonicalPost,
    PlatformName,
    MediaType,
    MediaMetadata,
    AuthorType,
    AccountAgeBucket,
    AuthorMetadata,
    EngagementMetrics,
)


class TwitterAdapter(PlatformAdapter):
    """Adapter for extracting content from Twitter/X"""
    
    def _initialize(self) -> None:
        """Initialize Twitter client"""
        self.bearer_token = self.config.get("bearer_token")
        self.use_api = bool(self.bearer_token)
        
        # Nitter instance (fallback for public scraping)
        self.nitter_instance = self.config.get("nitter_instance", "https://nitter.net")
        
        if self.use_api:
            # If using official API
            try:
                import tweepy
                self.client = tweepy.Client(bearer_token=self.bearer_token)
            except ImportError:
                print("Twitter adapter: tweepy not installed, falling back to scraping")
                self.use_api = False
                self.client = None
        else:
            # Using public scraping fallback
            self.client = None
            print("Twitter adapter: No API token, using public scraping fallback")
    
    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.TWITTER
    
    @property
    def url_pattern(self) -> re.Pattern:
        """Match Twitter/X post URLs"""
        return re.compile(
            r'https?://(?:www\.)?(twitter|x)\.com/(\w+)/status/(\d+)(?:\?.*)?'
        )
    
    def get_post_id_from_url(self, url: str) -> str:
        """Extract Twitter post ID from URL"""
        match = self.url_pattern.match(url)
        if not match:
            raise URLParseError(f"Invalid Twitter URL format: {url}")
        
        username = match.group(2)
        tweet_id = match.group(3)
        return f"twitter_{username}_{tweet_id}"
    
    async def extract(self, url: str) -> CanonicalPost:
        """
        Extract content from Twitter post URL.
        
        Tries API first (if available), falls back to scraping.
        """
        if not self.can_handle(url):
            raise URLParseError(f"This adapter cannot handle URL: {url}")
        
        if self.use_api:
            try:
                return await self._extract_via_api(url)
            except Exception as e:
                print(f"Twitter API failed, falling back to scraping: {e}")
                return await self._extract_via_scraping(url)
        else:
            return await self._extract_via_scraping(url)
    
    async def _extract_via_api(self, url: str) -> CanonicalPost:
        """Extract using official Twitter API"""
        try:
            # Extract tweet ID
            match = self.url_pattern.match(url)
            tweet_id = match.group(3)
            
            # Fetch tweet
            tweet = self.client.get_tweet(
                tweet_id,
                tweet_fields=['created_at', 'public_metrics', 'entities', 'attachments'],
                user_fields=['created_at', 'verified', 'public_metrics'],
                expansions=['author_id', 'attachments.media_keys'],
                media_fields=['url', 'preview_image_url', 'type'],
            )
            
            if not tweet.data:
                raise ContentExtractionError(f"Tweet not found: {url}")
            
            post_id = self.get_post_id_from_url(url)
            post_text = tweet.data.text
            timestamp = tweet.data.created_at
            
            # Extract author metadata
            author_metadata = None
            if tweet.includes and 'users' in tweet.includes:
                user = tweet.includes['users'][0]
                author_metadata = self._build_author_metadata_api(user)
            
            # Extract engagement
            metrics = tweet.data.public_metrics
            engagement_metrics = EngagementMetrics(
                likes=metrics.get('like_count', 0),
                shares=metrics.get('retweet_count', 0),
                replies=metrics.get('reply_count', 0),
                views=metrics.get('impression_count'),
            )
            
            # Extract media
            media_items = []
            if tweet.includes and 'media' in tweet.includes:
                media_items = self._extract_media_api(tweet.includes['media'])
            
            # Extract links
            external_links = []
            if tweet.data.entities and 'urls' in tweet.data.entities:
                external_links = [
                    url_entity['expanded_url'] 
                    for url_entity in tweet.data.entities['urls']
                    if 'expanded_url' in url_entity
                ]
            
            return CanonicalPost(
                post_id=post_id,
                post_text=post_text,
                platform_name=self.platform_name,
                timestamp=timestamp,
                language="en",
                author_metadata=author_metadata,
                engagement_metrics=engagement_metrics,
                media_items=media_items,
                external_links=external_links,
                raw_url=url,
                adapter_version=self._get_adapter_version(),
            )
        
        except Exception as e:
            raise ContentExtractionError(f"Failed to extract via Twitter API: {e}")
    
    async def _extract_via_scraping(self, url: str) -> CanonicalPost:
        """Extract using nitter scraping (fallback)"""
        try:
            from bs4 import BeautifulSoup
            
            # Convert Twitter URL to Nitter URL
            match = self.url_pattern.match(url)
            username = match.group(2)
            tweet_id = match.group(3)
            nitter_url = f"{self.nitter_instance}/{username}/status/{tweet_id}"
            
            # Fetch page
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(nitter_url, follow_redirects=True)
                response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract tweet content
            tweet_content = soup.find('div', class_='tweet-content')
            if not tweet_content:
                raise ContentExtractionError("Could not find tweet content in page")
            
            post_text = tweet_content.get_text(strip=True)
            post_id = self.get_post_id_from_url(url)
            
            # Extract engagement metrics (best-effort)
            engagement_metrics = self._extract_engagement_scraping(soup)
            
            # Extract media (best-effort)
            media_items = self._extract_media_scraping(soup)
            
            # Extract links (best-effort)
            external_links = []
            for link in tweet_content.find_all('a'):
                href = link.get('href', '')
                if href and href.startswith('http') and 'twitter.com' not in href and 'nitter' not in href:
                    external_links.append(href)
            
            return CanonicalPost(
                post_id=post_id,
                post_text=post_text,
                platform_name=self.platform_name,
                timestamp=datetime.utcnow(),  # Nitter doesn't always expose timestamp easily
                language="en",
                engagement_metrics=engagement_metrics,
                media_items=media_items,
                external_links=external_links[:10],
                raw_url=url,
                adapter_version=self._get_adapter_version(),
            )
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Nitter rate limit exceeded")
            raise ContentExtractionError(f"HTTP error: {e}")
        except Exception as e:
            raise ContentExtractionError(f"Failed to scrape tweet: {e}")
    
    def _build_author_metadata_api(self, user) -> AuthorMetadata:
        """Build author metadata from API user object"""
        # Account age
        account_age_days = (datetime.utcnow() - user.created_at).days
        if account_age_days < 30:
            age_bucket = AccountAgeBucket.NEW
        elif account_age_days < 180:
            age_bucket = AccountAgeBucket.RECENT
        elif account_age_days < 730:
            age_bucket = AccountAgeBucket.ESTABLISHED
        else:
            age_bucket = AccountAgeBucket.VETERAN
        
        # Follower bucket
        followers = user.public_metrics.get('followers_count', 0)
        if followers < 100:
            follower_bucket = "0-100"
        elif followers < 1000:
            follower_bucket = "100-1k"
        elif followers < 10000:
            follower_bucket = "1k-10k"
        elif followers < 100000:
            follower_bucket = "10k-100k"
        else:
            follower_bucket = "100k+"
        
        return AuthorMetadata(
            author_type=AuthorType.VERIFIED if user.verified else AuthorType.INDIVIDUAL,
            account_age_bucket=age_bucket,
            is_verified=user.verified,
            follower_count_bucket=follower_bucket,
        )
    
    def _extract_media_api(self, media_list) -> List[MediaMetadata]:
        """Extract media from API response"""
        media_items = []
        for media in media_list:
            if media.type == 'photo':
                media_items.append(MediaMetadata(
                    media_type=MediaType.IMAGE,
                    url=media.url,
                ))
            elif media.type == 'video' or media.type == 'animated_gif':
                media_items.append(MediaMetadata(
                    media_type=MediaType.VIDEO if media.type == 'video' else MediaType.GIF,
                    url=media.preview_image_url,  # Thumbnail
                ))
        return media_items
    
    def _extract_engagement_scraping(self, soup) -> Optional[EngagementMetrics]:
        """Extract engagement metrics from scraped page"""
        try:
            # Try to find stat counts in nitter HTML
            stats = soup.find_all('span', class_='icon-container')
            metrics = EngagementMetrics()
            
            for stat in stats:
                text = stat.get_text(strip=True)
                if text:
                    # Parse numeric values from stats
                    try:
                        value = int(text.replace(',', '').replace('K', '000').replace('M', '000000'))
                        # Assign based on icon type (limited parsing)
                        if not metrics.replies:
                            metrics.replies = value
                        elif not metrics.shares:
                            metrics.shares = value
                        elif not metrics.likes:
                            metrics.likes = value
                    except ValueError:
                        continue
            
            return metrics
        except Exception:
            return None
    
    def _extract_media_scraping(self, soup) -> List[MediaMetadata]:
        """Extract media from scraped page"""
        media_items = []
        try:
            # Images
            for img in soup.find_all('img', class_='still-image'):
                src = img.get('src', '')
                if src:
                    full_url = src if src.startswith('http') else f"{self.nitter_instance}{src}"
                    media_items.append(MediaMetadata(
                        media_type=MediaType.IMAGE,
                        url=full_url,
                    ))
            
            # Videos (thumbnails)
            for video in soup.find_all('video'):
                poster = video.get('poster', '')
                if poster:
                    full_url = poster if poster.startswith('http') else f"{self.nitter_instance}{poster}"
                    media_items.append(MediaMetadata(
                        media_type=MediaType.VIDEO,
                        url=full_url,
                    ))
        except Exception:
            pass
        return media_items
    
    async def extract_from_text(
        self, 
        raw_text: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> CanonicalPost:
        """Create CanonicalPost from pasted text"""
        import hashlib
        
        post_id = f"twitter_paste_{hashlib.md5(raw_text.encode()).hexdigest()[:12]}"
        
        return CanonicalPost(
            post_id=post_id,
            post_text=raw_text,
            platform_name=self.platform_name,
            timestamp=datetime.utcnow(),
            language="en",
            adapter_version=self._get_adapter_version(),
        )
    
    async def health_check(self) -> bool:
        """Check if adapter is functioning"""
        if self.use_api:
            try:
                self.client.get_me()
                return True
            except Exception:
                return False
        else:
            # Check if nitter instance is accessible
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(self.nitter_instance)
                    return response.status_code == 200
            except Exception:
                return False
