from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional

from ..helpers.enums import TemplateType
from ..core.OGImageService import OGImageService
from ..core.ResourceManager import ResourceManager
from ..helpers.TemplateFactory import TemplateFactory
from ..services.CacheService import CacheService
from ..helpers.db import db
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class OGImageController:
    """Controller for OG image endpoints."""
    
    def __init__(self, 
                 og_image_service: Optional[OGImageService] = None,
                 resource_manager: Optional[ResourceManager] = None):
        """
        Initialize the controller.
        
        Args:
            og_image_service: Optional OGImageService instance
            resource_manager: Optional ResourceManager instance
        """
        # Create resource manager if not provided
        self.resource_manager = resource_manager or ResourceManager()
        
        # Create OG image service if not provided
        self.og_image_service = og_image_service or OGImageService(
            resource_manager=self.resource_manager,
            template_factory=TemplateFactory(self.resource_manager),
            cache_service=CacheService()
        )
        
        # Create router
        self.router = APIRouter(prefix="/api/v1/og", tags=["OG Images"])
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register API routes."""
        
        @self.router.get("/news/{slug}")
        async def get_news_og(slug: str, background_tasks: BackgroundTasks):
            """Get OG image for a news article."""
            with tracer.start_as_current_span("get_news_og") as span:
                try:
                    span.set_attribute("news_slug", slug)
                    # Get news data from database
                    news_data = await db.get_news_by_slug(slug)
                    if not news_data:
                        raise HTTPException(status_code=404, detail="News not found")
                    
                    # Generate image
                    image_path = await self.og_image_service.generate_image(
                        TemplateType.NEWS, news_data
                    )
                    
                    # Add cleanup task
                    background_tasks.add_task(self._cleanup_temp_file, image_path)
                    
                    return FileResponse(image_path, media_type="image/webp")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
        
    async def _cleanup_temp_file(self, path: str):
        """Clean up temporary files."""
        try:
            import os
            os.unlink(path)
        except Exception as e:
            print(f"Error cleaning up temp file: {e}")
