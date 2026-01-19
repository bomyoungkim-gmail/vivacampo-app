from fastapi import FastAPI
from titiler.core.factory import TilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
import os

# Create FastAPI app
app = FastAPI(
    title="VivaCampo TiTiler",
    description="COG Tile Server for VivaCampo",
    version="1.0.0"
)

# Add exception handlers
add_exception_handlers(app, DEFAULT_STATUS_CODES)

# Configure AWS for LocalStack
if os.getenv("AWS_ENDPOINT_URL"):
    import boto3
    from botocore.config import Config
    
    boto3.setup_default_session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.getenv("AWS_REGION", "sa-east-1")
    )

# Create COG tiler
cog = TilerFactory(router_prefix="/cog")
app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])

@app.get("/")
def root():
    return {
        "service": "VivaCampo TiTiler",
        "version": "1.0.0",
        "endpoints": {
            "tiles": "/cog/tiles/{z}/{x}/{y}",
            "info": "/cog/info",
            "preview": "/cog/preview"
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
