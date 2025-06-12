import os
from typing import Optional

def initialize_opentelemetry(
    service_name: str = "default-service",
    endpoint: str = "http://localhost:4317",
    protocol: str = "grpc",
    enable_fastapi: bool = True,
    enable_pymongo: bool = True,
    enable_requests: bool = True
):
    """
    Initialize OpenTelemetry with configurable parameters instead of environment variables.
    
    Args:
        service_name: Name of the service
        endpoint: OTLP exporter endpoint
        protocol: OTLP protocol (grpc or http/protobuf)
        enable_fastapi: Whether to instrument FastAPI
        enable_pymongo: Whether to instrument PyMongo
        enable_requests: Whether to instrument Requests
    """
    # Set up resource attributes with service name
    from opentelemetry.sdk.resources import Resource
    resource = Resource.create({"service.name": service_name})
    
    # tracing setup
    from opentelemetry.trace import set_tracer_provider, get_tracer_provider
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    
    if protocol.lower() == "grpc":
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        span_exporter = OTLPSpanExporter(endpoint=endpoint)
    else:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        span_exporter = OTLPSpanExporter(endpoint=endpoint)
    
    tracer_provider = TracerProvider(resource=resource)
    span_processor = BatchSpanProcessor(span_exporter)
    tracer_provider.add_span_processor(span_processor)
    set_tracer_provider(tracer_provider)

    # metrics setup
    from opentelemetry.metrics import set_meter_provider, get_meter_provider
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    
    if protocol.lower() == "grpc":
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        metric_exporter = OTLPMetricExporter(endpoint=endpoint)
    else:
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        metric_exporter = OTLPMetricExporter(endpoint=endpoint)
    
    reader = PeriodicExportingMetricReader(
        metric_exporter,
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[reader],
    )
    set_meter_provider(meter_provider)

    # instrumentations
    if enable_fastapi:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor().instrument()
    
    if enable_pymongo:
        from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
        PymongoInstrumentor().instrument()
    
    if enable_requests:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().instrument()
    
    print(f"OTEL setup completed ✅ (service: {service_name}, endpoint: {endpoint})")


# For backward compatibility with environment variables
def initialize_opentelemetry_from_env():
    """
    Initialize OpenTelemetry using environment variables:
    - OTEL_SERVICE_NAME or service.name from OTEL_RESOURCE_ATTRIBUTES
    - OTEL_EXPORTER_OTLP_ENDPOINT
    - OTEL_EXPORTER_OTLP_PROTOCOL
    """
    # Extract service name
    service_name = os.environ.get("OTEL_SERVICE_NAME", "default-service")
    
    # Try to get from OTEL_RESOURCE_ATTRIBUTES if OTEL_SERVICE_NAME is not set
    if service_name == "default-service" and "OTEL_RESOURCE_ATTRIBUTES" in os.environ:
        attrs = os.environ.get("OTEL_RESOURCE_ATTRIBUTES", "")
        for attr in attrs.split(','):
            if attr.startswith("service.name="):
                service_name = attr.split("=", 1)[1]
                break
    
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    protocol = os.environ.get("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    
    return initialize_opentelemetry(
        service_name=service_name,
        endpoint=endpoint,
        protocol=protocol
    )