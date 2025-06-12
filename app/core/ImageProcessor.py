from PIL import Image, ImageDraw
from typing import Optional, Tuple, Union
from io import BytesIO
import gc


class ImageProcessor:
    """Utility class for common image processing operations."""
    
    @staticmethod
    def optimize_image(image_data: Union[bytes, str], max_size: Tuple[int, int] = (800, 800)) -> Image.Image:
        """
        Optimize an image from downloaded data or file path.
        
        Args:
            image_data: Raw image data (bytes) or path to image file
            max_size: Maximum dimensions to resize the image to
            
        Returns:
            A PIL Image object that has been optimized
        """
        try:
            # Load image from bytes or file
            if isinstance(image_data, bytes):
                img = Image.open(BytesIO(image_data))
            else:
                img = Image.open(image_data)
            
            # Convert to RGB or RGBA as needed
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA')
                
            # Check if resizing is needed
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
            # Force garbage collection
            gc.collect()
            
            return img
        except Exception as e:
            print(f"Error optimizing image: {e}")
            # Return a small blank image as fallback
            return Image.new('RGBA', (100, 100), (200, 200, 200, 255))
    
    @staticmethod
    def apply_circular_mask(image: Image.Image) -> Image.Image:
        """
        Apply a circular mask to an image.
        
        Args:
            image: The image to mask
            
        Returns:
            Image with circular mask applied
        """
        # Create a circular mask
        mask = Image.new("L", image.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)
        
        # Apply mask to make image circular
        circular_img = Image.new("RGBA", image.size, (0, 0, 0, 0))
        circular_img.paste(image, (0, 0), mask)
        
        # Clean up
        del mask
        del mask_draw
        
        return circular_img
    
    @staticmethod
    def create_gradient(width: int, height: int, 
                        start_color: Tuple[int, int, int, int], 
                        end_color: Tuple[int, int, int, int], 
                        direction: str = 'vertical') -> Image.Image:
        """
        Create a gradient image.
        
        Args:
            width: Width of the gradient
            height: Height of the gradient
            start_color: Starting color as RGBA tuple
            end_color: Ending color as RGBA tuple
            direction: 'vertical' or 'horizontal'
            
        Returns:
            Gradient image
        """
        # Create base image
        gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)
        
        # Draw gradient
        if direction == 'vertical':
            for y in range(height):
                # Calculate color at this position
                r = int(start_color[0] + (end_color[0] - start_color[0]) * (y / height))
                g = int(start_color[1] + (end_color[1] - start_color[1]) * (y / height))
                b = int(start_color[2] + (end_color[2] - start_color[2]) * (y / height))
                a = int(start_color[3] + (end_color[3] - start_color[3]) * (y / height))
                
                # Draw line
                draw.line([(0, y), (width, y)], fill=(r, g, b, a))
        else:  # horizontal
            for x in range(width):
                # Calculate color at this position
                r = int(start_color[0] + (end_color[0] - start_color[0]) * (x / width))
                g = int(start_color[1] + (end_color[1] - start_color[1]) * (x / width))
                b = int(start_color[2] + (end_color[2] - start_color[2]) * (x / width))
                a = int(start_color[3] + (end_color[3] - start_color[3]) * (x / width))
                
                # Draw line
                draw.line([(x, 0), (x, height)], fill=(r, g, b, a))
        
        return gradient
    
    @staticmethod
    def wrap_text(text: str, font, max_width: int) -> list:
        """
        Breaks text into lines that fit within max_width using the specified font.
        
        Args:
            text: Text to wrap
            font: Font to use for measuring text
            max_width: Maximum width in pixels
            
        Returns:
            List of text lines
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            # Try adding the word to the current line
            test_line = ' '.join(current_line + [word])
            # Check if the line width exceeds max_width
            bbox = font.getbbox(test_line)
            line_width = bbox[2] - bbox[0]  # width = right - left

            if line_width <= max_width:
                # Word fits, add it to the current line
                current_line.append(word)
            else:
                # Word doesn't fit, start a new line
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Edge case: single word is wider than max_width
                    lines.append(word)
                    current_line = []

        # Add the last line if it's not empty
        if current_line:
            lines.append(' '.join(current_line))

        return lines