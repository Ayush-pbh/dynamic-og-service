from abc import ABC, abstractmethod
from PIL import Image, ImageDraw
from typing import Dict, Any, Optional, Tuple
import os
from pathlib import Path

from ...helpers.enums import TemplateType, ImageFormat, ImageQuality
from ...helpers.constants import (
    GENERATED_DIR, TEMPLATE_DIMENSIONS, WEBP_QUALITY, WEBP_METHOD
)
from ..ResourceManager import ResourceManager


class ImageTemplate(ABC):
    """
    Abstract base class for all image templates.
    Provides common functionality for template rendering and saving.
    """
    
    def __init__(self, 
                 template_type: TemplateType,
                 resource_manager: ResourceManager,
                 width: Optional[int] = None,
                 height: Optional[int] = None,
                 background_color: Optional[Tuple[int, int, int]] = None):
        """
        Initialize the template.
        
        Args:
            template_type: The type of template
            resource_manager: ResourceManager instance for loading assets
            width: Optional width override (if not using standard template)
            height: Optional height override (if not using standard template)
            background_color: Optional background color as RGB tuple
        """
        self.template_type = template_type
        self.resource_manager = resource_manager
        
        # Use provided dimensions or default to optimized size
        self.width = width or TEMPLATE_DIMENSIONS["optimized"][0]
        self.height = height or TEMPLATE_DIMENSIONS["optimized"][1]
        
        # Calculate scaling factor based on original template dimensions
        original_width, original_height = TEMPLATE_DIMENSIONS["original"]
        self.scale_factor = self.height / original_height
        
        # Initialize image and draw objects
        self.image = None
        self.draw = None
        self.background_color = background_color
        
        # Flag to track if template has been rendered
        self.is_rendered = False
    
    def initialize_canvas(self):
        """
        Initialize the canvas for drawing.
        This can be overridden by subclasses to use different initialization methods.
        """
        if self.background_color:
            self.image = Image.new('RGB', (self.width, self.height), color=self.background_color)
        else:
            # Load template from resource manager
            try:
                self.image = self.resource_manager.get_template(self.template_type)
                
                # Resize if needed
                if (self.image.width != self.width or self.image.height != self.height):
                    self.image = self.image.resize((self.width, self.height), Image.Resampling.LANCZOS)
            except Exception as e:
                # Fallback to blank image if template loading fails
                print(f"Failed to load template: {e}")
                self.image = Image.new('RGB', (self.width, self.height), color=(255, 255, 255))
        
        # Create draw object
        self.draw = ImageDraw.Draw(self.image)
    
    @abstractmethod
    def render(self, data: Dict[str, Any]) -> None:
        """
        Render the template with the provided data.
        Must be implemented by subclasses.
        
        Args:
            data: Dictionary containing the data to render
        """
        pass
    
    def save(self, 
             output_path: Optional[str] = None, 
             format: ImageFormat = ImageFormat.WEBP,
             quality: int = WEBP_QUALITY) -> str:
        """
        Save the rendered image to disk.
        
        Args:
            output_path: Path where to save the image. If None, a default path is generated.
            format: Image format to use
            quality: Image quality (0-100)
            
        Returns:
            Path to the saved image
        """
        if not self.is_rendered:
            raise ValueError("Template has not been rendered yet. Call render() first.")
        
        if not self.image:
            raise ValueError("No image to save. Template initialization failed.")
        
        # Generate default output path if none provided
        if output_path is None:
            os.makedirs(GENERATED_DIR, exist_ok=True)
            output_path = str(GENERATED_DIR / f"{self.template_type.value}.{format.value}")
        
        # Convert to RGB if saving as JPEG
        if format == ImageFormat.JPEG and self.image.mode == 'RGBA':
            rgb_img = Image.new('RGB', self.image.size, (255, 255, 255))
            rgb_img.paste(self.image, mask=self.image.split()[3])
            rgb_img.save(output_path, format.value.upper(), quality=quality)
        elif format == ImageFormat.WEBP:
            # Use optimized settings for WEBP
            self.image.save(output_path, format.value.upper(), 
                           quality=quality, method=WEBP_METHOD)
        else:
            self.image.save(output_path, format.value.upper(), quality=quality)
        
        return output_path
    
    def scale_dimension(self, original_size: int) -> int:
        """
        Scale a dimension based on the template's scale factor.
        
        Args:
            original_size: Original size to scale
            
        Returns:
            Scaled size
        """
        return int(original_size * self.scale_factor)
    
    def scale_position(self, x: int, y: int) -> Tuple[int, int]:
        """
        Scale a position based on the template's scale factor.
        
        Args:
            x: Original x coordinate
            y: Original y coordinate
            
        Returns:
            Tuple of scaled (x, y) coordinates
        """
        return (self.scale_dimension(x), self.scale_dimension(y))
    
    def scale_size(self, width: int, height: int) -> Tuple[int, int]:
        """
        Scale a size based on the template's scale factor.
        
        Args:
            width: Original width
            height: Original height
            
        Returns:
            Tuple of scaled (width, height)
        """
        return (self.scale_dimension(width), self.scale_dimension(height))
    
    def get_scaled_font_size(self, original_size: int) -> int:
        """
        Get a scaled font size based on the template's scale factor.
        
        Args:
            original_size: Original font size
            
        Returns:
            Scaled font size (minimum 12)
        """
        return max(int(original_size * self.scale_factor), 12)