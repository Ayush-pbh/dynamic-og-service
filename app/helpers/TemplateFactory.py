from typing import Optional, Dict, Any

from .enums import TemplateType
from ..core.ResourceManager import ResourceManager
from ..core.image_template.UserTemplate import UserTemplate
from ..core.image_template.PostTemplate import PostTemplate
from ..core.image_template.NewsTemplate import NewsTemplate
from ..core.image_template.IdeaTemplate import IdeaTemplate
from ..core.email_template.InvoiceTemplate import InvoiceTemplate
from ..core.image_template.base import ImageTemplate

from opentelemetry import trace

tracer = trace.get_tracer(__name__)

class TemplateFactory:
    """Factory for creating appropriate template instances."""
    
    def __init__(self, resource_manager: ResourceManager):
        """
        Initialize the template factory.
        
        Args:
            resource_manager: ResourceManager instance for loading assets
        """
        self.resource_manager = resource_manager
    
    def create_template(self, template_type: TemplateType, data: Optional[Dict[str, Any]] = None) -> ImageTemplate:
        """
        Create and return the appropriate template instance.
        
        Args:
            template_type: Type of template to create
            data: Optional data that might be needed for template initialization
            
        Returns:
            An instance of the appropriate template class
            
        Raises:
            ValueError: If template_type is not supported
        """
        with tracer.start_as_current_span("create_template") as span:
            span.set_attribute("template_type", template_type.value)
            if template_type == TemplateType.NEWS:
                return NewsTemplate(self.resource_manager)
            else:
                raise ValueError(f"Unsupported template type: {template_type}")