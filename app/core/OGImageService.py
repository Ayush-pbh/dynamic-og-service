from typing import Dict, Any, Optional
import os
import gc

from ..helpers.enums import TemplateType, ImageFormat, CacheStrategy
from ..helpers.constants import GENERATED_DIR, WEBP_QUALITY
from .ResourceManager import ResourceManager
from ..helpers.TemplateFactory import TemplateFactory
from ..services.CacheService import CacheService
from opentelemetry import trace, metrics

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

counter_total = meter.create_counter(
    name="og_image_tasks_total",
    unit="1",
    description="The number of OG images generated",
)
counter_news_og = meter.create_counter(
    name="news_og_tasks",
    unit="1",
    description="The number of News OG images generated",
)

class OGImageService:
    """Main service for generating OG images."""
    
    def __init__(self, 
                 resource_manager: ResourceManager,
                 template_factory: Optional[TemplateFactory] = None,
                 cache_service: Optional[CacheService] = None):
        """
        Initialize the OG image service.
        
        Args:
            resource_manager: ResourceManager instance for loading assets
            template_factory: Optional TemplateFactory instance
            cache_service: Optional CacheService instance
        """
        self.resource_manager = resource_manager
        
        # Create template factory if not provided
        self.template_factory = template_factory or TemplateFactory(resource_manager)
        
        # Create cache service if not provided
        self.cache_service = cache_service or CacheService(
            strategy=CacheStrategy.DISK,
            cache_dir=GENERATED_DIR
        )
    
    async def generate_image(self, 
                            template_type: TemplateType, 
                            data: Dict[str, Any],
                            force_regenerate: bool = False) -> str:
        """
        Generate an OG image.
        
        Args:
            template_type: Type of template to use
            data: Data to use for rendering the template
            force_regenerate: Whether to force regeneration even if cached
            
        Returns:
            Path to the generated image
        """
        with tracer.start_as_current_span("generate_image") as span:
            span.set_attribute("template_type", template_type.value)
            span.set_attribute("force_regenerate", force_regenerate)
            # Create cache key
            cache_key = self._create_cache_key(template_type, data)
            
            # Check cache if not forcing regeneration
            if not force_regenerate:
                cached_path = await self.cache_service.get_cached_image(cache_key)
                if cached_path:
                    return cached_path
            # Create appropriate template
            template = self.template_factory.create_template(template_type, data)   
            try:
                render_span = tracer.start_span("render_template")
                render_span.set_attribute("template_type", template_type.value)
                # Render the template
                template.render(data)
                render_span.end()
            except Exception as e:
                span.record_exception(e)
                print(f"Error rendering template for {template_type}: {e}")
                raise e
            # Generate output path
            try:
                output_path = template.get_output_path(data)
            except Exception as e:
                span.record_exception(e)
                print(f"Error getting output path for {template_type}: {e}")
                raise e
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the image
            try:
                template.save(output_path, format=ImageFormat.WEBP, quality=WEBP_QUALITY)
            except Exception as e:
                span.record_exception(e)
                print(f"Error saving image for {template_type}: {e}")
                raise e
            
            # Save to cache
            await self.cache_service.save_to_cache(output_path, cache_key)
            
            # Clean up
            del template
            
            # Increment counter
            counter_total.add(1)
            if template_type == TemplateType.NEWS:
                counter_news_og.add(1)
            
            gc.collect()
            return output_path
    
    def _create_cache_key(self, template_type: TemplateType, data: Dict[str, Any]) -> str:
        """
        Create a cache key for the given template type and data.
        
        Args:
            template_type: Template type
            data: Template data
            
        Returns:
            Cache key string
        """
        if template_type == TemplateType.NEWS:
            return f"news_{data.get('slug', 'unknown')}"
        else:
            return f"{template_type.value}_{hash(str(data))}"