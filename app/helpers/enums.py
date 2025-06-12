"""
This module contains enums for various constants and configurations used throughout the application.
"""
from enum import Enum, auto
from typing import Optional


class TemplateType(Enum):
    """Enum for different types of OG image templates"""
    NEWS = "news"

class ImageFormat(Enum):
    """Enum for supported image formats"""
    WEBP = "webp"
    PNG = "png"
    JPEG = "jpeg"


class ImageQuality(Enum):
    """Enum for image quality presets"""
    LOW = 30
    MEDIUM = 60
    HIGH = 90


class CacheStrategy(Enum):
    """Enum for caching strategies"""
    MEMORY = auto()
    DISK = auto()
    S3 = auto()
    NONE = auto()
