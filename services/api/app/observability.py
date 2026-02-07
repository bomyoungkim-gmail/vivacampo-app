"""OpenTelemetry setup for API service."""
from __future__ import annotations

import structlog

from app.config import settings
from app.database import engine

logger = structlog.get_logger()


def setup_tracing(app) -> None:
    if not settings.otel_enabled:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    except ModuleNotFoundError:
        logger.warning("opentelemetry_not_installed_skipping_tracing")
        return

    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    if settings.otel_endpoint:
        exporter = OTLPSpanExporter(endpoint=settings.otel_endpoint)
    else:
        logger.warning("otel_endpoint_missing_using_console_exporter")
        exporter = ConsoleSpanExporter()

    provider.add_span_processor(BatchSpanProcessor(exporter))

    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)
