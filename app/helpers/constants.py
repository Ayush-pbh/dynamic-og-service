"""Constants for the application."""
import os
from pathlib import Path
from typing import Dict, Tuple

# Get the project root directory (assuming constants.py is in app/core)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Base directories
ASSETS_DIR = PROJECT_ROOT / "app/assets"
GENERATED_DIR = PROJECT_ROOT / "generated"

# Ensure directories exist
ASSETS_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)



# Font paths - use relative paths from ASSETS_DIR
FONT_PATHS = {
    "bold": "SourceSans3-Bold.ttf",
    "medium": "SourceSans3-Medium.ttf",
    "regular": "SourceSans3.ttf",
}

# Default font sizes
DEFAULT_FONT_SIZES = {
    "title": 400,
    "subtitle": 300,
    "body": 250,
    "small": 100,
}

# Image dimensions
TEMPLATE_DIMENSIONS: Dict[str, Tuple[int, int]] = {
    "original": (15001, 7875),  # Original template size
    "optimized": (2280, 1200),  # Optimized template size
    "user": (1200, 1200),      # Square user template
}

# Cache settings
CACHE_TIMEOUT = 120  # seconds
MAX_CACHE_SIZE = 5   # items

# S3 settings
S3_BUCKET = os.getenv("AWS_S3_BUCKET", "")
S3_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BASE_URL = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/"

# Image processing settings
MAX_IMAGE_SIZE = (800, 800)  # Maximum size for downloaded images
WEBP_QUALITY = 40           # Default WEBP quality
WEBP_METHOD = 6             # WEBP compression method (6 is faster and uses less memory)

# HTTP settings
HTTP_TIMEOUT = 5  # seconds
