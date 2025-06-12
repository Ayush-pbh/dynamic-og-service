from fastapi import FastAPI
import gc

from app.helpers.enums import CacheStrategy
from .core.ResourceManager import ResourceManager
from .helpers.TemplateFactory import TemplateFactory
from .services.CacheService import CacheService
from .core.OGImageService import OGImageService
from .controller.OGImageController import OGImageController
from .helpers.notifier import Notifier
from .helpers.db import db
from .otel_setup import initialize_opentelemetry
import os

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    # Create app
    app = FastAPI(
        title="Medial Image Service",
        description="Service for optimizing images and generating Open Graph images",
        version="1.0.1"
    )
    
    # Create shared resources
    resource_manager = ResourceManager()
    template_factory = TemplateFactory(resource_manager)
    cache_service = CacheService(strategy=CacheStrategy.S3)
    notifier = Notifier()
    notifier.register_slack("warnings", os.getenv("SLACK_WEBHOOK", ""))
    
    # Create OG service
    og_image_service = OGImageService(
        resource_manager=resource_manager,
        template_factory=template_factory,
        cache_service=cache_service
    )
    
    
    # Create controller
    og_controller = OGImageController(og_image_service)
    
    # Create Health Check Route
    app.add_api_route("/checks/healthz", lambda: "OK", methods=["GET"])
    
    # Register routes
    app.include_router(og_controller.router)
    
    # Add startup and shutdown events
    @app.on_event("startup")
    async def startup():
        # Ensure necessary directories exist
        from .helpers.constants import GENERATED_DIR, ASSETS_DIR
        import os
        os.makedirs(GENERATED_DIR, exist_ok=True)
        os.makedirs(ASSETS_DIR, exist_ok=True)
        
        # Initialize database connection
        await db.connect()
    
    @app.on_event("shutdown")
    async def shutdown():
        # Clean up resources
        resource_manager.clear_caches()
        # Close database connection
        await db.close()
        gc.collect()
    
    return app

n = Notifier()
n.register_slack("warnings", os.getenv("SLACK_WEBHOOK_URL", ""))

# Initialize opentelemetry
try:
    initialize_opentelemetry()
except Exception as e:
    n.send("Failed to initialize OpenTelemetry", "warnings","warning", code_block=str(e))
    print("Failed to initialize OpenTelemetry")

# Create the FastAPI application instance
app = create_app()
