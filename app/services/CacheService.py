import os
import time
from typing import Optional, Dict
from pathlib import Path
import boto3
import gc

from ..helpers.enums import CacheStrategy
from ..helpers.constants import (
    GENERATED_DIR, S3_BUCKET, S3_REGION, S3_BASE_URL,
    CACHE_TIMEOUT
)

from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class CacheService:
    """Service for caching generated images."""
    
    def __init__(self, 
                 strategy: CacheStrategy = CacheStrategy.DISK,
                 cache_dir: Path = GENERATED_DIR,
                 cache_timeout: int = CACHE_TIMEOUT):
        """
        Initialize the cache service.
        
        Args:
            strategy: Caching strategy to use
            cache_dir: Directory for disk cache
            cache_timeout: Time in seconds after which cached items expire
        """
        self.strategy = strategy
        self.cache_dir = cache_dir
        self.cache_timeout = cache_timeout
        
        # Create cache directory if it doesn't exist
        if self.strategy == CacheStrategy.DISK:
            os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize S3 client if using S3 strategy
        self.s3_client = None
        if self.strategy == CacheStrategy.S3:
            self.s3_client = boto3.client('s3')
    
    async def get_cached_image(self, key: str) -> Optional[str]:
        """
        Get a cached image if it exists and is not expired.
        
        Args:
            key: Cache key (e.g., "user_john-doe")
            
        Returns:
            Path to cached image or None if not found or expired
        """
        with tracer.start_as_current_span("get_cached_image") as span:
            span.set_attribute("cache_key", key)
            # Check cache strategy
            if self.strategy == CacheStrategy.NONE:
                return None
            
            elif self.strategy == CacheStrategy.DISK:
                return self._get_from_disk_cache(key)
            
            elif self.strategy == CacheStrategy.S3:
                return self._get_from_s3_cache(key)
            
            return None
    
    async def save_to_cache(self, image_path: str, key: str) -> Optional[str]:
        """
        Save an image to the cache.
        
        Args:
            image_path: Path to the image file
            key: Cache key
            
        Returns:
            URL or path to the cached image, or None if caching failed
        """
        with tracer.start_as_current_span("save_to_cache") as span:
            span.set_attribute("cache_key", key)
            if self.strategy == CacheStrategy.NONE:
                return None
            
            elif self.strategy == CacheStrategy.DISK:
                return image_path  # Already saved to disk
            
            elif self.strategy == CacheStrategy.S3:
                return self._save_to_s3(image_path, key)
            
            return None
    
    def _get_from_disk_cache(self, key: str) -> Optional[str]:
        """
        Get an image from the disk cache.
        
        Args:
            key: Cache key
            
        Returns:
            Path to cached image or None if not found or expired
        """
        # Check for webp file
        cache_path = self.cache_dir / f"{key}.webp"
        
        if cache_path.exists():
            # Check if file is expired
            file_age = time.time() - os.path.getmtime(cache_path)
            if file_age < self.cache_timeout:
                return str(cache_path)
        
        return None
    
    def _get_from_s3_cache(self, key: str) -> Optional[str]:
        """
        Get an image from S3 cache.
        
        Args:
            key: Cache key
            
        Returns:
            URL to cached image or None if not found
        """
        with tracer.start_as_current_span("get_from_s3_cache") as span:
            span.set_attribute("cache_key", key)
            if not self.s3_client or not S3_BUCKET:
                return None
            
            try:
                # Check if object exists in S3
                self.s3_client.head_object(Bucket=S3_BUCKET, Key=f"{key}.webp")
                return f"{S3_BASE_URL}{key}.webp"
            except Exception:
                return None
    
    def _save_to_s3(self, image_path: str, key: str) -> Optional[str]:
        """
        Save an image to S3.
        
        Args:
            image_path: Path to the image file
            key: Cache key
            
        Returns:
            URL to the S3 object or None if upload failed
        """
        with tracer.start_as_current_span("save_to_s3") as span:
            span.set_attribute("cache_key", key)
            if not self.s3_client or not S3_BUCKET:
                return None
            
            try:
                # Set content type and caching headers
                extra_args = {
                    'ContentType': 'image/webp',
                    'CacheControl': 'max-age=31536000'  # Cache for 1 year
                }
                
                # Upload file to S3
                s3_key = f"{key}.webp"
                self.s3_client.upload_file(
                    image_path, 
                    S3_BUCKET, 
                    s3_key,
                    ExtraArgs=extra_args
                )
                
                return f"{S3_BASE_URL}{s3_key}"
            except Exception as e:
                print(f"Error uploading to S3: {e}")
                return None
    
    def clear_cache(self):
        """Clear the cache."""
        if self.strategy == CacheStrategy.DISK:
            # Delete all files in cache directory
            for file_path in self.cache_dir.glob("*.webp"):
                try:
                    os.unlink(file_path)
                except Exception as e:
                    print(f"Error deleting cache file {file_path}: {e}")
            
            # Force garbage collection
            gc.collect()