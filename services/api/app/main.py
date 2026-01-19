from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from app.config import settings

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
app = FastAPI(
    title="VivaCampo API",
    description="Multi-tenant Earth Observation platform for agricultural monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

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
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("unhandled_exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            }
        }
    )


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
    system_admin_router, weather_router
)

app.include_router(auth_router.router, prefix="/v1", tags=["auth"])
app.include_router(farms_router.router, prefix="/v1/app", tags=["farms"])
app.include_router(aois_router.router, prefix="/v1/app", tags=["aois"])
app.include_router(jobs_router.router, prefix="/v1/app", tags=["jobs"])
app.include_router(signals_router.router, prefix="/v1/app", tags=["signals"])
app.include_router(weather_router.router, prefix="/v1/app", tags=["weather"])
app.include_router(ai_assistant_router.router, prefix="/v1/app", tags=["ai-assistant"])
app.include_router(tenant_admin_router.router, prefix="/v1/app", tags=["tenant-admin"])
app.include_router(system_admin_router.router, prefix="/v1", tags=["system-admin"])
