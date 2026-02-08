"""
Image Feature Extraction

Extracts useful features from images:
1. Image Captioning - Describe what's in the image
2. OCR - Extract text from image
3. Basic metadata - Dimensions, format

These features are sent to Gemini as text, not raw images.
This controls cost and latency while maintaining multimodal capability.
"""

from pathlib import Path
from typing import Optional
from PIL import Image

from src.core.schemas import MediaFeatures


class ImageFeatureExtractor:
    """Extract features from images"""
    
    def __init__(self):
        """Initialize feature extractor"""
        # Check if tesseract is available
        self.ocr_available = False
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self.ocr_available = True
            self._pytesseract = pytesseract
        except Exception:
            print("Warning: Tesseract not found. OCR will be disabled.")
            self._pytesseract = None
    
    async def extract_features(self, image_path: Path) -> MediaFeatures:
        """
        Extract all features from an image.
        
        Args:
            image_path: Path to cached image file
        
        Returns:
            MediaFeatures with caption and OCR text
        """
        try:
            # Open image
            image = Image.open(image_path)
            
            # Extract OCR text
            ocr_text = self._extract_ocr_text(image) if self.ocr_available else None
            
            # Generate caption (simplified for MVP)
            caption = self._generate_simple_caption(image, ocr_text)
            
            # Detect faces (basic - disabled for MVP)
            face_detected = None
            
            return MediaFeatures(
                caption=caption,
                ocr_text=ocr_text,
                face_detected=face_detected,
            )
        
        except Exception as e:
            print(f"Error extracting image features: {e}")
            # Return minimal features on error
            return MediaFeatures(
                caption="Image processing failed",
            )
    
    def _extract_ocr_text(self, image: Image.Image) -> Optional[str]:
        """
        Extract text from image using OCR.
        
        Args:
            image: PIL Image
        
        Returns:
            Extracted text or None
        """
        if not self._pytesseract:
            return None
            
        try:
            # Perform OCR
            text = self._pytesseract.image_to_string(image)
            
            # Clean up text
            text = text.strip()
            
            # Only return if substantial text found
            if len(text) > 10:
                # Truncate if too long
                if len(text) > 2000:
                    text = text[:2000] + "..."
                return text
            
            return None
        
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return None
    
    def _generate_simple_caption(
        self, 
        image: Image.Image, 
        ocr_text: Optional[str]
    ) -> str:
        """
        Generate a simple caption for the image.
        
        For MVP, this is rule-based. In production, you might use:
        - BLIP (image captioning model)
        - CLIP (image-text matching)
        - Gemini Vision API
        
        Args:
            image: PIL Image
            ocr_text: OCR text if available
        
        Returns:
            Simple caption
        """
        width, height = image.size
        format_name = image.format or "unknown"
        
        # Build caption parts
        caption_parts = [f"Image ({width}x{height}, {format_name})"]
        
        # Add OCR hint
        if ocr_text and len(ocr_text) > 0:
            caption_parts.append("contains text")
        
        # Check if screenshot-like (wide aspect ratio, large size)
        aspect_ratio = width / max(height, 1)
        if aspect_ratio > 1.5 and width > 800:
            caption_parts.append("appears to be a screenshot")
        elif aspect_ratio < 0.7 and height > 800:
            caption_parts.append("appears to be a portrait/mobile screenshot")
        
        # Check color mode
        if image.mode == 'L':
            caption_parts.append("grayscale")
        elif image.mode == 'RGBA':
            caption_parts.append("with transparency")
        
        return ", ".join(caption_parts)
    
    def get_image_metadata(self, image_path: Path) -> dict:
        """
        Get basic image metadata.
        
        Args:
            image_path: Path to image
        
        Returns:
            Dict with width, height, format, size
        """
        try:
            image = Image.open(image_path)
            return {
                'width': image.width,
                'height': image.height,
                'format': image.format,
                'mode': image.mode,
                'size_bytes': image_path.stat().st_size,
            }
        except Exception as e:
            return {
                'error': str(e)
            }
