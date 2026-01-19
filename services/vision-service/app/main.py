"""
Vision Service - Main Application

FastAPI application for image-based analysis:
- Cattle/Swine weight estimation
- Crop disease detection
- Poultry health assessment

Supports TensorFlow Lite for optimized inference.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import settings
from app.api import router as vision_router
from app.inference.predictor import get_predictor

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("starting_vision_service", env=settings.env)

    # Pre-load models (optional, for faster first request)
    if settings.env != "local":
        predictor = get_predictor()
        logger.info("models_preloaded")

    yield

    # Shutdown
    logger.info("shutting_down_vision_service")


# Create FastAPI app
app = FastAPI(
    title="VivaCampo Vision API",
    description="""
    Computer Vision API for agricultural monitoring.

    ## Features

    ### Animal Weight Estimation
    - **Cattle (Bovine)**: Estimate weight from side-view images
    - **Swine (Pigs)**: Estimate weight for pork production

    ### Crop Disease Detection
    - Identify diseases in soybean, corn, coffee, citrus, cotton, sugarcane
    - Get severity levels and treatment recommendations

    ### Poultry Health Assessment
    - Detect health issues in chickens and turkeys
    - Get health scores and recommended actions

    ## TensorFlow Lite Support
    All models are available in TFLite format for mobile/offline inference.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
    ] if settings.env == "local" else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("unhandled_exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.env == "local" else None,
        },
    )


# Health check (root level)
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "vision-service"}


# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "VivaCampo Vision API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "analyze": "/v1/vision/analyze",
            "cattle_weight": "/v1/vision/cattle/weight",
            "swine_weight": "/v1/vision/swine/weight",
            "crop_disease": "/v1/vision/crop/disease",
            "poultry_health": "/v1/vision/poultry/health",
        },
    }


# Register routers
app.include_router(vision_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.env == "local",
    )
