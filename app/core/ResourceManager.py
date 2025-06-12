from PIL import Image, ImageFont
from typing import Dict, Tuple, Optional
import gc
import time
import threading
from pathlib import Path

from ..helpers.enums import TemplateType, ImageFormat
from ..helpers.constants import (
    ASSETS_DIR, TEMPLATE_PATHS, IDEA_TEMPLATES,
    CACHE_TIMEOUT, MAX_CACHE_SIZE
)


class ResourceManager:
    """
    Manages resources like templates, fonts, and other assets.
    Implements a caching mechanism to avoid loading the same resources multiple times.
    """
    
    def __init__(self, 
                 cache_timeout: int = CACHE_TIMEOUT,
                 max_cache_size: int = MAX_CACHE_SIZE,
                 assets_dir: Path = ASSETS_DIR):
        """
        Initialize the ResourceManager.
        
        Args:
            cache_timeout: Time in seconds after which cached resources expire
            max_cache_size: Maximum number of items to keep in each cache
            assets_dir: Directory where assets (templates, fonts) are stored
        """
        self._templates: Dict[str, Tuple[Image.Image, float]] = {}
        self._fonts: Dict[str, Tuple[ImageFont.FreeTypeFont, float]] = {}
        self._lock = threading.Lock()
        self._cache_timeout = cache_timeout
        self._max_cache_size = max_cache_size
        
        # Convert assets_dir to absolute path if it's relative
        self._assets_dir = Path(assets_dir).resolve()
        
        # Ensure assets directory exists
        if not self._assets_dir.exists():
            raise ValueError(f"Assets directory not found: {self._assets_dir}")
            
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def get_template(self, template_type: TemplateType, month_index: Optional[int] = None) -> Image.Image:
        """
        Get a template image, either from cache or by loading it from disk.
        
        Args:
            template_type: Type of template from TemplateType enum
            month_index: Optional month index (0-11) for idea templates
                           
        Returns:
            A copy of the template image
        """
        current_time = time.time()
        template_key = template_type.value
        
        # Handle special case for idea templates which depend on month
        if template_type == TemplateType.IDEA and month_index is not None:
            if not 0 <= month_index < 12:
                raise ValueError(f"Month index must be between 0 and 11, got {month_index}")
            template_path = IDEA_TEMPLATES[month_index]
            template_key = f"{template_type.value}_{month_index}"
        elif template_type.value in TEMPLATE_PATHS:
            template_path = TEMPLATE_PATHS[template_type.value]
        else:
            raise ValueError(f"No template path defined for {template_type}")
        
        with self._lock:
            # Check if we need to trim the cache before adding a new item
            if len(self._templates) >= self._max_cache_size and template_key not in self._templates:
                self._trim_cache(self._templates)
                
            if template_key in self._templates:
                template, _ = self._templates[template_key]
                self._templates[template_key] = (template, current_time)
                return template.copy()
            
            # Load template with optimized settings
            try:
                template = Image.open(template_path).convert("RGBA")
                self._templates[template_key] = (template, current_time)
                return template.copy()
            except Exception as e:
                raise ValueError(f"Failed to load template {template_type} from {template_path}: {e}")
    
    def get_font(self, font_path: str, size: int) -> ImageFont.FreeTypeFont:
        """
        Get a font, either from cache or by loading it from disk.
        
        Args:
            font_path: Path to the font file
            size: Font size in points
            
        Returns:
            The font object
        """
        cache_key = f"{font_path}_{size}"
        current_time = time.time()
        
        with self._lock:
            # Check if we need to trim the cache before adding a new item
            if len(self._fonts) >= self._max_cache_size and cache_key not in self._fonts:
                self._trim_cache(self._fonts)
                
            if cache_key in self._fonts:
                font, _ = self._fonts[cache_key]
                self._fonts[cache_key] = (font, current_time)
                return font
            
            try:
                # Convert relative path to absolute path using assets_dir
                absolute_font_path = self._assets_dir / font_path
                if not absolute_font_path.exists():
                    raise FileNotFoundError(f"Font file not found: {absolute_font_path}")
                
                font = ImageFont.truetype(str(absolute_font_path), size)
                self._fonts[cache_key] = (font, current_time)
                return font
            except Exception as e:
                raise ValueError(f"Failed to load font from {font_path} at size {size}: {e}")
    
    def get_asset_path(self, asset_name: str) -> str:
        """
        Get the full path to an asset.
        
        Args:
            asset_name: Name of the asset file
            
        Returns:
            Full path to the asset
        """
        return str(self._assets_dir / asset_name)
    
    def _trim_cache(self, cache_dict: Dict):
        """
        Remove the oldest item from the cache.
        
        Args:
            cache_dict: The cache dictionary to trim
        """
        if not cache_dict:
            return
            
        # Find the oldest item
        oldest_key = None
        oldest_time = float('inf')
        
        for key, (_, timestamp) in cache_dict.items():
            if timestamp < oldest_time:
                oldest_time = timestamp
                oldest_key = key
                
        if oldest_key:
            del cache_dict[oldest_key]
            gc.collect()  # Force garbage collection after removing an item
    
    def _cleanup_loop(self):
        """Background thread that periodically cleans up expired resources."""
        while True:
            time.sleep(30)  # Check every 30 seconds
            self._cleanup_resources()
    
    def _cleanup_resources(self):
        """Remove expired resources from caches."""
        current_time = time.time()
        
        with self._lock:
            # Cleanup templates
            expired_templates = [
                key for key, (_, timestamp) in self._templates.items()
                if current_time - timestamp > self._cache_timeout
            ]
            for key in expired_templates:
                del self._templates[key]
            
            # Cleanup fonts
            expired_fonts = [
                key for key, (_, timestamp) in self._fonts.items()
                if current_time - timestamp > self._cache_timeout
            ]
            for key in expired_fonts:
                del self._fonts[key]
        
        # Force garbage collection
        gc.collect()
    
    def clear_caches(self):
        """Clear all caches. Useful for testing or when memory needs to be freed."""
        with self._lock:
            self._templates.clear()
            self._fonts.clear()
        gc.collect()
