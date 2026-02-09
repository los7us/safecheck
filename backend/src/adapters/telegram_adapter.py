"""
Telegram Platform Adapter

Extracts content from public Telegram channels/groups and normalizes
to CanonicalPost schema.

Supported URL formats:
- https://t.me/{channel}/{message_id}
- https://t.me/{channel}

Limitations:
- Public channels and groups ONLY
- No private chats or encrypted messages
- No video/audio processing
- Single post analysis only

Uses Telethon library for Telegram API access.
Requires api_id and api_hash from telegram.org.
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime

from src.adapters.base_adapter import (
    PlatformAdapter,
    URLParseError,
    ContentExtractionError,
)
from src.core.schemas import (
    CanonicalPost,
    PlatformName,
    MediaType,
    MediaMetadata,
    AuthorType,
    AccountAgeBucket,
    AuthorMetadata,
)


class TelegramAdapter(PlatformAdapter):
    """Adapter for extracting content from public Telegram channels/groups"""
    
    # URL pattern: https://t.me/{channel}/{message_id} or https://t.me/{channel}
    _URL_PATTERN = re.compile(
        r'https?://(?:www\.)?t\.me/([a-zA-Z0-9_]+)(?:/(\d+))?'
    )
    
    def _initialize(self) -> None:
        """Initialize Telegram client"""
        self.api_id = self.config.get("api_id")
        self.api_hash = self.config.get("api_hash")
        self._client = None
        
        if not self.api_id or not self.api_hash:
            print("Warning: Telegram API credentials not configured")
    
    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.TELEGRAM
    
    @property
    def url_pattern(self) -> re.Pattern:
        """Match Telegram post URLs"""
        return self._URL_PATTERN
    
    def get_post_id_from_url(self, url: str) -> str:
        """Extract Telegram channel and message ID from URL"""
        match = self._URL_PATTERN.match(url)
        if not match:
            raise URLParseError(f"Invalid Telegram URL: {url}")
        
        channel = match.group(1)
        message_id = match.group(2)  # May be None
        
        if message_id:
            return f"{channel}/{message_id}"
        return channel
    
    async def extract(self, url: str) -> CanonicalPost:
        """
        Extract content from Telegram public channel/group URL.
        
        Args:
            url: Telegram URL (t.me/channel/message_id)
        
        Returns:
            CanonicalPost with normalized data
        
        Raises:
            URLParseError: If URL format is invalid
            ContentExtractionError: If content cannot be retrieved
        """
        match = self._URL_PATTERN.match(url)
        if not match:
            raise URLParseError(f"Invalid Telegram URL: {url}")
        
        channel_name = match.group(1)
        message_id = match.group(2)
        
        if not message_id:
            raise URLParseError(
                f"Message ID required. Use format: https://t.me/{channel_name}/123"
            )
        
        try:
            # Try to extract using Telethon if available
            if self.api_id and self.api_hash:
                return await self._extract_via_telethon(channel_name, int(message_id), url)
            else:
                # Fallback: try public preview (limited data)
                return await self._extract_via_preview(channel_name, int(message_id), url)
                
        except Exception as e:
            raise ContentExtractionError(f"Failed to extract Telegram message: {e}")
    
    async def _extract_via_telethon(
        self, 
        channel_name: str, 
        message_id: int,
        original_url: str
    ) -> CanonicalPost:
        """Extract using Telethon library"""
        try:
            from telethon import TelegramClient
            from telethon.tl.types import Channel, Chat, Message
        except ImportError:
            raise ContentExtractionError(
                "Telethon not installed. Run: pip install telethon"
            )
        
        # Create client (session stored in memory)
        client = TelegramClient(
            'safecheck_session',
            int(self.api_id),
            self.api_hash
        )
        
        try:
            await client.start()
            
            # Get the channel/chat entity
            try:
                entity = await client.get_entity(channel_name)
            except Exception as e:
                raise ContentExtractionError(
                    f"Cannot access channel '{channel_name}': {e}. "
                    "Make sure it's a public channel."
                )
            
            # Check if public
            is_public = False
            channel_type = "unknown"
            
            if isinstance(entity, Channel):
                is_public = entity.username is not None
                channel_type = "public_channel" if entity.broadcast else "public_group"
            elif isinstance(entity, Chat):
                # Regular group - check if it has public link
                is_public = hasattr(entity, 'username') and entity.username is not None
                channel_type = "public_group"
            
            if not is_public:
                raise ContentExtractionError(
                    f"Channel '{channel_name}' is private. Only public content is supported."
                )
            
            # Get the specific message
            message = await client.get_messages(entity, ids=message_id)
            
            if not message:
                raise ContentExtractionError(
                    f"Message {message_id} not found in {channel_name}"
                )
            
            # Extract media
            media_items = []
            if message.photo:
                # Download photo to get URL
                media_items.append(MediaMetadata(
                    media_type=MediaType.IMAGE,
                    url=f"telegram://photo/{channel_name}/{message_id}",
                ))
            
            # Build author metadata
            author_metadata = AuthorMetadata(
                author_type=AuthorType.ORGANIZATION if isinstance(entity, Channel) and entity.broadcast else AuthorType.INDIVIDUAL,
                account_age_bucket=AccountAgeBucket.UNKNOWN,
                is_verified=getattr(entity, 'verified', False),
            )
            
            # Build post text
            post_text = message.text or message.message or ""
            if not post_text and message.photo:
                post_text = "[Image post without text]"
            
            # Create CanonicalPost
            return CanonicalPost(
                post_id=f"tg_{channel_name}_{message_id}",
                post_text=post_text,
                platform_name=PlatformName.TELEGRAM,
                timestamp=message.date,
                author_metadata=author_metadata,
                media_items=media_items if media_items else None,
                external_links=self._extract_links(post_text),
                adapter_version="telegram_1.0",
                raw_metadata={
                    "channel": channel_name,
                    "channel_type": channel_type,
                    "is_forwarded": message.fwd_from is not None,
                    "is_reply": message.reply_to is not None,
                    "views": message.views,
                    "forwards": message.forwards,
                }
            )
            
        finally:
            await client.disconnect()
    
    async def _extract_via_preview(
        self,
        channel_name: str,
        message_id: int,
        original_url: str
    ) -> CanonicalPost:
        """
        Fallback extraction using t.me embed preview.
        Limited data but works without API credentials.
        """
        import aiohttp
        from bs4 import BeautifulSoup
        
        # Try the embed URL
        embed_url = f"https://t.me/{channel_name}/{message_id}?embed=1"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(embed_url, timeout=10) as response:
                    if response.status != 200:
                        raise ContentExtractionError(
                            f"Telegram returned {response.status}. "
                            "Channel may be private or message deleted."
                        )
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract message text
            text_div = soup.find('div', class_='tgme_widget_message_text')
            post_text = text_div.get_text(strip=True) if text_div else ""
            
            if not post_text:
                # Check for forwarded/unavailable
                if "This channel" in html and "private" in html.lower():
                    raise ContentExtractionError(
                        f"Channel '{channel_name}' is private. Only public content is supported."
                    )
                post_text = "[Unable to extract message text]"
            
            # Extract image if present
            media_items = []
            photo_wrap = soup.find('a', class_='tgme_widget_message_photo_wrap')
            if photo_wrap:
                style = photo_wrap.get('style', '')
                # Extract URL from background-image style
                import re
                url_match = re.search(r"url\(['\"]?([^'\"]+)['\"]?\)", style)
                if url_match:
                    media_items.append(MediaMetadata(
                        media_type=MediaType.IMAGE,
                        url=url_match.group(1),
                    ))
            
            # Extract timestamp
            time_elem = soup.find('time')
            timestamp = None
            if time_elem and time_elem.get('datetime'):
                try:
                    timestamp = datetime.fromisoformat(
                        time_elem['datetime'].replace('Z', '+00:00')
                    )
                except:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()
            
            # Extract channel title
            author_elem = soup.find('span', class_='tgme_widget_message_author')
            author_name = author_elem.get_text(strip=True) if author_elem else channel_name
            
            return CanonicalPost(
                post_id=f"tg_{channel_name}_{message_id}",
                post_text=post_text,
                platform_name=PlatformName.TELEGRAM,
                timestamp=timestamp,
                author_metadata=AuthorMetadata(
                    author_type=AuthorType.ORGANIZATION,
                    account_age_bucket=AccountAgeBucket.UNKNOWN,
                ),
                media_items=media_items if media_items else None,
                external_links=self._extract_links(post_text),
                adapter_version="telegram_preview_1.0",
                raw_metadata={
                    "channel": channel_name,
                    "channel_type": "public_channel",
                    "author_name": author_name,
                }
            )
            
        except aiohttp.ClientError as e:
            raise ContentExtractionError(f"Network error accessing Telegram: {e}")
    
    def _extract_links(self, text: str) -> Optional[list]:
        """Extract URLs from text"""
        if not text:
            return None
        
        url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+'
        )
        links = url_pattern.findall(text)
        return links if links else None
    
    async def extract_from_text(
        self,
        raw_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CanonicalPost:
        """
        Create CanonicalPost from pasted text (fallback mode).
        
        Used when user pastes Telegram content instead of URL.
        """
        return CanonicalPost(
            post_id=f"tg_paste_{hash(raw_text) % 100000:05d}",
            post_text=raw_text,
            platform_name=PlatformName.TELEGRAM,
            timestamp=datetime.utcnow(),
            adapter_version="telegram_paste_1.0",
            raw_metadata=context,
        )
    
    async def health_check(self) -> bool:
        """Check if Telegram adapter is configured"""
        if not self.api_id or not self.api_hash:
            return False
        
        # Just check credentials are set, don't make API call
        return True
