"""
Reddit Platform Adapter

Extracts content from Reddit posts and normalizes to CanonicalPost schema.

Uses PRAW (Python Reddit API Wrapper) for data extraction.

Supported URL formats:
- https://reddit.com/r/subreddit/comments/post_id/...
- https://www.reddit.com/r/subreddit/comments/post_id/...
- https://old.reddit.com/r/subreddit/comments/post_id/...
"""

import re
from typing import Optional, Dict, Any, List
from datetime import datetime
import praw
from praw.models import Submission

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


class RedditAdapter(PlatformAdapter):
    """Adapter for extracting content from Reddit"""
    
    def _initialize(self) -> None:
        """Initialize Reddit API client"""
        client_id = self.config.get("client_id")
        client_secret = self.config.get("client_secret")
        user_agent = self.config.get("user_agent", "SafetyCheck/1.0")
        
        if not client_id or not client_secret:
            raise ValueError("Reddit credentials not provided in config")
        
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )
            # Set to read-only mode
            self.reddit.read_only = True
        except Exception as e:
            raise ValueError(f"Failed to initialize Reddit client: {e}")
    
    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.REDDIT
    
    @property
    def url_pattern(self) -> re.Pattern:
        """Match Reddit post URLs"""
        return re.compile(
            r'https?://(?:www\.)?(?:old\.)?reddit\.com/r/(\w+)/comments/(\w+)/?.*'
        )
    
    def get_post_id_from_url(self, url: str) -> str:
        """Extract Reddit post ID from URL"""
        match = self.url_pattern.match(url)
        if not match:
            raise URLParseError(f"Invalid Reddit URL format: {url}")
        
        subreddit_name = match.group(1)
        post_id = match.group(2)
        return f"reddit_{subreddit_name}_{post_id}"
    
    async def extract(self, url: str) -> CanonicalPost:
        """
        Extract content from Reddit post URL.
        
        Extracts:
        - Post title and selftext
        - Author metadata (account age, karma bucket)
        - Engagement metrics (upvotes, comments)
        - Media content (images, videos)
        - Top comments (sampled)
        - Subreddit context
        """
        if not self.can_handle(url):
            raise URLParseError(f"This adapter cannot handle URL: {url}")
        
        try:
            # Get submission from Reddit
            submission = self.reddit.submission(url=url)
            
            # Extract data
            post_id = self.get_post_id_from_url(url)
            post_text = self._build_post_text(submission)
            timestamp = self._extract_timestamp(submission)
            author_metadata = self._extract_author_metadata(submission)
            engagement_metrics = self._extract_engagement_metrics(submission)
            media_items = self._extract_media(submission)
            external_links = self._extract_external_links(submission)
            sampled_comments = self._sample_comments(submission)
            
            return CanonicalPost(
                post_id=post_id,
                post_text=post_text,
                platform_name=self.platform_name,
                timestamp=timestamp,
                language="en",  # Reddit is predominantly English
                author_metadata=author_metadata,
                engagement_metrics=engagement_metrics,
                media_items=media_items,
                external_links=external_links,
                sampled_comments=sampled_comments,
                raw_url=url,
                adapter_version=self._get_adapter_version(),
            )
        
        except praw.exceptions.InvalidURL:
            raise ContentExtractionError(f"Invalid Reddit URL: {url}")
        except Exception as e:
            # Check for prawcore HTTP exceptions
            error_str = str(e).lower()
            if '404' in error_str or 'not found' in error_str:
                raise ContentExtractionError(f"Reddit post not found: {url}")
            elif '403' in error_str or 'forbidden' in error_str:
                raise ContentExtractionError(f"Access forbidden (private/deleted): {url}")
            elif '429' in error_str or 'rate limit' in error_str or 'too many' in error_str:
                raise RateLimitError("Reddit API rate limit exceeded")
            else:
                raise ContentExtractionError(f"Failed to extract Reddit content: {e}")
    
    def _build_post_text(self, submission: Submission) -> str:
        """Build combined post text from title and body"""
        parts = [submission.title]
        
        if submission.selftext and submission.selftext.strip():
            parts.append(submission.selftext)
        
        return "\n\n".join(parts)
    
    def _extract_timestamp(self, submission: Submission) -> datetime:
        """Extract post creation timestamp"""
        return datetime.fromtimestamp(submission.created_utc)
    
    def _extract_author_metadata(self, submission: Submission) -> Optional[AuthorMetadata]:
        """Extract author metadata (non-PII)"""
        if not submission.author:
            return None
        
        try:
            author = submission.author
            
            # Determine account age bucket
            account_age_days = (datetime.utcnow().timestamp() - author.created_utc) / 86400
            if account_age_days < 30:
                age_bucket = AccountAgeBucket.NEW
            elif account_age_days < 180:
                age_bucket = AccountAgeBucket.RECENT
            elif account_age_days < 730:
                age_bucket = AccountAgeBucket.ESTABLISHED
            else:
                age_bucket = AccountAgeBucket.VETERAN
            
            # Karma bucket (privacy-preserving)
            total_karma = author.link_karma + author.comment_karma
            if total_karma < 100:
                karma_bucket = "0-100"
            elif total_karma < 1000:
                karma_bucket = "100-1k"
            elif total_karma < 10000:
                karma_bucket = "1k-10k"
            elif total_karma < 100000:
                karma_bucket = "10k-100k"
            else:
                karma_bucket = "100k+"
            
            return AuthorMetadata(
                author_type=AuthorType.INDIVIDUAL,
                account_age_bucket=age_bucket,
                is_verified=author.is_gold or author.is_mod,
                follower_count_bucket=karma_bucket,  # Using karma as proxy
            )
        except Exception:
            return None
    
    def _extract_engagement_metrics(self, submission: Submission) -> EngagementMetrics:
        """Extract public engagement metrics"""
        return EngagementMetrics(
            likes=max(0, submission.score),  # Upvotes minus downvotes
            replies=submission.num_comments,
            views=None,  # Reddit doesn't expose view counts
        )
    
    def _extract_media(self, submission: Submission) -> List[MediaMetadata]:
        """Extract media URLs from post"""
        media_items = []
        
        # Image posts
        if hasattr(submission, 'post_hint') and submission.post_hint == 'image':
            media_items.append(MediaMetadata(
                media_type=MediaType.IMAGE,
                url=submission.url,
            ))
        
        # Gallery posts
        elif hasattr(submission, 'is_gallery') and submission.is_gallery:
            if hasattr(submission, 'media_metadata') and submission.media_metadata:
                for item in submission.media_metadata.values():
                    if 's' in item and 'u' in item['s']:
                        media_items.append(MediaMetadata(
                            media_type=MediaType.IMAGE,
                            url=item['s']['u'].replace('&amp;', '&'),
                        ))
        
        # Video posts
        elif hasattr(submission, 'is_video') and submission.is_video:
            if hasattr(submission, 'media') and submission.media:
                reddit_video = submission.media.get('reddit_video', {})
                if reddit_video.get('fallback_url'):
                    media_items.append(MediaMetadata(
                        media_type=MediaType.VIDEO,
                        url=reddit_video['fallback_url'],
                    ))
        
        return media_items
    
    def _extract_external_links(self, submission: Submission) -> List[str]:
        """Extract external links from post"""
        links = []
        
        # Link posts
        if not submission.is_self and submission.url:
            # Filter out Reddit's own CDN and known safe domains
            if not any(domain in submission.url for domain in ['redd.it', 'reddit.com', 'i.redd.it']):
                links.append(submission.url)
        
        # Links in selftext (basic extraction)
        if submission.selftext:
            url_pattern = re.compile(r'https?://[^\s\)]+')
            found_urls = url_pattern.findall(submission.selftext)
            for url in found_urls:
                if not any(domain in url for domain in ['reddit.com', 'redd.it']):
                    links.append(url)
        
        return links[:10]  # Limit to 10 links
    
    def _sample_comments(self, submission: Submission, max_comments: int = 5) -> List[str]:
        """Sample top comments for context"""
        comments = []
        
        try:
            submission.comment_sort = 'top'
            submission.comments.replace_more(limit=0)  # Don't expand "load more"
            
            for comment in submission.comments[:max_comments]:
                if hasattr(comment, 'body') and comment.body and len(comment.body) > 10:
                    # Truncate long comments
                    comment_text = comment.body[:500]
                    if len(comment.body) > 500:
                        comment_text += "..."
                    comments.append(comment_text)
        except Exception:
            # Comments are optional, don't fail if they can't be fetched
            pass
        
        return comments
    
    async def extract_from_text(
        self, 
        raw_text: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> CanonicalPost:
        """
        Create CanonicalPost from pasted text (fallback mode).
        
        Used when user pastes content instead of URL.
        """
        import hashlib
        
        # Generate pseudo-ID from content hash
        post_id = f"reddit_paste_{hashlib.md5(raw_text.encode()).hexdigest()[:12]}"
        
        return CanonicalPost(
            post_id=post_id,
            post_text=raw_text,
            platform_name=self.platform_name,
            timestamp=datetime.utcnow(),
            language="en",
            adapter_version=self._get_adapter_version(),
        )
    
    async def health_check(self) -> bool:
        """Check if Reddit API is accessible"""
        try:
            # Try to access Reddit frontpage
            list(self.reddit.subreddit('python').hot(limit=1))
            return True
        except Exception:
            return False
