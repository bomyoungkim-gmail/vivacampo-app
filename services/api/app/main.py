from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from app.config import settings
import uuid

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Create FastAPI app
def _custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    components = openapi_schema.setdefault("components", {}).setdefault("schemas", {})
    components["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "details": {"type": "object"},
                    "traceId": {"type": "string"},
                },
                "required": ["code", "message"],
            }
        },
        "required": ["error"],
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI(
    title="VivaCampo API",
    description="Multi-tenant Earth Observation platform for agricultural monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.openapi = _custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3002", "http://localhost:3000"] if settings.env == "local" else [],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)

# Rate limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.middleware.rate_limit import limiter

app.state.limiter = limiter
class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        structlog.contextvars.clear_contextvars()
        return response


app.add_middleware(RequestIdMiddleware)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return _error_response(
        status_code=429,
        message="Rate limit exceeded",
        details={"limit": str(getattr(exc, "detail", ""))},
        trace_id=getattr(request.state, "request_id", None),
    )


app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


def _error_code_for_status(status_code: int) -> str:
    return {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
    }.get(status_code, "HTTP_ERROR")


def _error_response(status_code: int, message: str, details: dict | None = None, trace_id: str | None = None):
    payload = {
        "error": {
            "code": _error_code_for_status(status_code),
            "message": message,
        }
    }
    if details:
        payload["error"]["details"] = details
    if trace_id:
        payload["error"]["traceId"] = trace_id
    return JSONResponse(status_code=status_code, content=payload)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)
    return _error_response(exc.status_code, str(detail), trace_id=getattr(request.state, "request_id", None))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _error_response(
        status_code=422,
        message="Validation error",
        details={"errors": exc.errors()},
        trace_id=getattr(request.state, "request_id", None),
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("unhandled_exception", exc_info=exc, path=request.url.path)
    return _error_response(500, "An unexpected error occurred", trace_id=getattr(request.state, "request_id", None))


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.env
    }


# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "VivaCampo API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    from app.metrics import get_metrics
    return get_metrics()


# Register routers
from app.presentation import (
    auth_router, farms_router, aois_router, jobs_router,
    signals_router, ai_assistant_router, tenant_admin_router,
    system_admin_router, weather_router, radar_router, tiles_router, nitrogen_router, correlation_router
)

app.include_router(auth_router.router, prefix="/v1", tags=["auth"])
app.include_router(farms_router.router, prefix="/v1/app", tags=["farms"])
app.include_router(aois_router.router, prefix="/v1/app", tags=["aois"])
app.include_router(jobs_router.router, prefix="/v1/app", tags=["jobs"])
app.include_router(signals_router.router, prefix="/v1/app", tags=["signals"])
app.include_router(weather_router.router, prefix="/v1/app", tags=["weather"])
app.include_router(radar_router.router, prefix="/v1/app", tags=["radar"])
app.include_router(nitrogen_router.router, prefix="/v1/app", tags=["nitrogen"])
app.include_router(correlation_router.router, prefix="/v1/app", tags=["correlation"])
app.include_router(ai_assistant_router.router, prefix="/v1/app", tags=["ai-assistant"])
app.include_router(tenant_admin_router.router, prefix="/v1/app", tags=["tenant-admin"])
app.include_router(system_admin_router.router, prefix="/v1", tags=["system-admin"])
app.include_router(tiles_router.router, prefix="/v1", tags=["tiles"])
