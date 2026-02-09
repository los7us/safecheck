"""
Image Upload Handler (VISION-ENABLED)

Handles uploaded screenshots and prepares them for Gemini Vision analysis.

Process:
1. Validate image file
2. Save to temporary location
3. Return CanonicalPost AND image path for vision analysis
"""

from pathlib import Path
from typing import Optional, Tuple
import hashlib
import io
from datetime import datetime

from PIL import Image
import aiofiles

from src.core.schemas import (
    CanonicalPost,
    PlatformName,
    MediaMetadata,
    MediaType,
)


class ImageUploadException(Exception):
    """Exception for image upload errors"""
    pass


class ImageUploadHandler:
    """Handles screenshot uploads for vision-based analysis"""
    
    def __init__(self, upload_dir: Path, max_size_mb: int = 10):
        """
        Initialize image upload handler.
        
        Args:
            upload_dir: Directory for temporary image storage
            max_size_mb: Maximum upload size in MB
        """
        self.upload_dir = Path(upload_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_upload(
        self,
        file_content: bytes,
        filename: str,
        user_context: Optional[str] = None,
    ) -> Tuple[CanonicalPost, Path]:
        """
        Process an uploaded image and create CanonicalPost.
        
        UPDATED: Now returns image path for Gemini Vision analysis.
        
        Args:
            file_content: Raw image bytes
            filename: Original filename
            user_context: Optional user-provided context about the image
        
        Returns:
            Tuple of (CanonicalPost, image_path) for vision analysis
        
        Raises:
            ImageUploadException: If processing fails
        """
        # Validate size
        if len(file_content) > self.max_size_bytes:
            raise ImageUploadException(
                f"File too large: {len(file_content) / 1024 / 1024:.1f}MB "
                f"(max: {self.max_size_bytes / 1024 / 1024:.0f}MB)"
            )
        
        # Validate image format
        try:
            image = Image.open(io.BytesIO(file_content))
            width, height = image.size
            image.verify()
        except Exception as e:
            raise ImageUploadException(f"Invalid image file: {e}")
        
        # Generate unique ID
        content_hash = hashlib.sha256(file_content).hexdigest()
        upload_id = f"upload_{content_hash[:12]}"
        
        # Save image file
        image_path = await self._save_temp_file(file_content, filename, content_hash)
        
        # Build post text from user context
        # (Gemini Vision will read text from the image directly)
        post_text = self._build_post_text(user_context)
        
        # Create media metadata
        media_metadata = MediaMetadata(
            media_type=MediaType.IMAGE,
            url=str(image_path),
            hash=content_hash,
            width=width,
            height=height,
            size_bytes=len(file_content),
        )
        
        # Create CanonicalPost (simplified - no OCR features needed)
        post = CanonicalPost(
            post_id=upload_id,
            post_text=post_text,
            platform_name=PlatformName.UNKNOWN,
            timestamp=datetime.utcnow(),
            media_items=[media_metadata],
            # No media_features - Gemini Vision will see the actual image
            adapter_version="image_upload_vision_2.0",
        )
        
        return post, image_path
    
    async def _save_temp_file(
        self,
        content: bytes,
        filename: str,
        content_hash: str,
    ) -> Path:
        """Save uploaded file temporarily."""
        # Get extension
        ext = Path(filename).suffix.lower()
        if not ext:
            ext = '.png'
        
        # Ensure valid extension
        allowed_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        if ext not in allowed_exts:
            raise ImageUploadException(f"Unsupported file type: {ext}")
        
        # Create temp filename
        temp_filename = f"{content_hash}{ext}"
        temp_path = self.upload_dir / temp_filename
        
        # Save file
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(content)
        
        return temp_path
    
    def _build_post_text(self, user_context: Optional[str]) -> str:
        """
        Build post text from user context.
        
        Since Gemini Vision can read text from images directly,
        we only need user-provided context here.
        """
        if user_context and user_context.strip():
            return f"User context: {user_context.strip()}"
        return "Screenshot uploaded for analysis"
    
    async def cleanup_old_uploads(self, max_age_hours: int = 24) -> int:
        """
        Remove uploaded files older than max_age_hours.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of files removed
        """
        import time
        
        now = time.time()
        max_age_seconds = max_age_hours * 3600
        
        removed_count = 0
        for file_path in self.upload_dir.iterdir():
            if file_path.is_file():
                age = now - file_path.stat().st_mtime
                if age > max_age_seconds:
                    file_path.unlink()
                    removed_count += 1
        
        return removed_count
