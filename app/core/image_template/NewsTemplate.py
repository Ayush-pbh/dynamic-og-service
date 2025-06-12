from PIL import Image, ImageDraw, ImageOps
from typing import Dict, Any, Optional, Tuple
import requests
from io import BytesIO
import gc
import numpy as np
from .base import ImageTemplate
from ...helpers.enums import TemplateType
from ...helpers.constants import (
    FONT_PATHS, GENERATED_DIR, MAX_IMAGE_SIZE, 
    HTTP_TIMEOUT, TEMPLATE_DIMENSIONS
)
from ..ImageProcessor  import ImageProcessor


class NewsTemplate(ImageTemplate):
    """Template for generating news article OG images."""
    
    def __init__(self, resource_manager, **kwargs):
        """Initialize the news template."""
        super().__init__(TemplateType.NEWS, resource_manager=resource_manager, **kwargs)
    
    def initialize_canvas(self):
        """
        Override to create a black canvas instead of loading a template.
        News template is generated dynamically with a background image.
        """
        # Create a black canvas
        self.image = Image.fromarray(np.zeros((self.height, self.width, 3), dtype=np.uint8))
        self.draw = ImageDraw.Draw(self.image)
    
    def render(self, data: Dict[str, Any]) -> None:
        """
        Render the news template with the provided data.
        
        Args:
            data: Dictionary containing news data with keys:
                - title: News article title
                - imageUrl: URL to the background image
                - brand: Optional brand name
                - slug: News article slug (for output filename)
        """
        print(data)
        # Initialize canvas
        self.initialize_canvas()
        
        # Get image URL
        image_url = data.get("imageUrl")
        if not image_url:
            raise ValueError("No imageUrl provided in data")
        
        try:
            # Download and process background image
            bg_img = self._process_background_image(image_url)
            
            if bg_img:
                # Paste background onto the canvas
                self.image.paste(bg_img, (0, 0))
                
                # Free up memory
                del bg_img
                gc.collect()
        except Exception as e:
            print(f"Error processing background image: {e}")
        
        # Get image dimensions
        img_width, img_height = self.image.size
        
        # Load fonts with scaled sizes
        original_font_size = 580
        original_brand_font_size = 200
        
        font_title = self.resource_manager.get_font(
            FONT_PATHS["bold"], 
            self.get_scaled_font_size(original_font_size)
        )
        font_brand = self.resource_manager.get_font(
            FONT_PATHS["medium"], 
            self.get_scaled_font_size(original_brand_font_size)
        )
        
        # Create gradient overlay for text readability
        fade_height = int(img_height * 0.4)  # 40% of image height
        
        # Create black-to-transparent gradient
        gradient = ImageProcessor.create_gradient(
            img_width, fade_height,
            (0, 0, 0, 0),    # Black, fully transparent
            (0, 0, 0, 255),  # Black, fully opaque
            'vertical'
        )
        
        # Paste gradient at bottom of image
        self.image.paste(gradient, (0, img_height - fade_height), gradient)
        
        # Free up memory
        del gradient
        gc.collect()
        
        # Draw title
        headline = data.get('title', 'Read News on Medial')
        headline = headline[:101] + '...' if len(headline) > 101 else headline
        
        # Wrap text to fit width
        wrapped_title = ImageProcessor.wrap_text(
            headline, font_title, img_width - self.scale_dimension(400)
        )
        
        # Draw wrapped title
        y_offset = img_height - fade_height + self.scale_dimension(100)
        for line in wrapped_title:
            line_width = self.draw.textlength(line, font=font_title)
            x_pos = (img_width - line_width) // 2
            self.draw.text((x_pos, y_offset), line, font=font_title, fill="white")
            line_height = self.draw.textbbox((0, 0), line, font=font_title)[3]
            y_offset += line_height + self.scale_dimension(20)
        
        # Draw brand name if provided
        if 'brand' in data:
            brand = data['brand']
            self.draw.text(
                self.scale_position(120, 120), 
                brand, 
                font=font_brand, 
                fill="black"
            )
        
        # Mark as rendered
        self.is_rendered = True
    
    def _process_background_image(self, image_url: str) -> Optional[Image.Image]:
        """
        Download and process a background image.
        
        Args:
            image_url: URL to the background image
            
        Returns:
            Processed image or None if processing failed
        """
        try:
            # Download image with timeout
            response = requests.get(image_url, timeout=HTTP_TIMEOUT)
            
            if response.status_code == 200:
                # Optimize the image
                bg_img = ImageProcessor.optimize_image(response.content, MAX_IMAGE_SIZE)
                
                # Resize to fit canvas (object-fit: cover)
                bg_img = ImageOps.fit(
                    bg_img, 
                    (self.width, self.height), 
                    method=Image.Resampling.LANCZOS
                )
                
                return bg_img
            else:
                raise Exception(f"Failed to download background image: {response.status_code}")
        except Exception as e:
            print(f"Error processing background image: {e}")
            
        return None
    
    def get_output_path(self, data: Dict[str, Any]) -> str:
        """
        Generate the output path for the rendered image.
        
        Args:
            data: News data dictionary
            
        Returns:
            Output path
        """
        slug = data.get('slug', 'news')
        return str(GENERATED_DIR / f"news_{slug}.webp")