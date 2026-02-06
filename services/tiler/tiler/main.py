"""
VivaCampo TiTiler Service

COG and Mosaic tile server with support for:
- Cloud Optimized GeoTIFFs (COG)
- MosaicJSON for virtual aggregation
- Planetary Computer integration
- On-the-fly vegetation index calculation
"""

import os

# IMPORTANT: Configure AWS/GDAL environment BEFORE importing rasterio/rio-tiler
# This ensures GDAL picks up the LocalStack configuration
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
AWS_REGION = os.getenv("AWS_REGION", "sa-east-1")

if AWS_ENDPOINT_URL:
    # Set GDAL/rasterio environment for LocalStack S3 access
    os.environ["AWS_S3_ENDPOINT"] = AWS_ENDPOINT_URL
    os.environ["AWS_HTTPS"] = "NO"
    os.environ["AWS_VIRTUAL_HOSTING"] = "FALSE"
    os.environ["AWS_REQUEST_PAYER"] = "requester"
    # Also set for GDAL directly
    os.environ["GDAL_HTTP_UNSAFESSL"] = "YES"
    os.environ["CPL_VSIL_USE_TEMP_FILE_FOR_RANDOM_WRITE"] = "YES"

# Now import everything else
from typing import Annotated, Literal, Optional
from urllib.parse import urlparse

import planetary_computer
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from titiler.core.factory import TilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.mosaic.factory import MosaicTilerFactory
from titiler.core.dependencies import DatasetPathParams
from starlette.requests import Request
from starlette.responses import Response

from .expressions import (
    VEGETATION_INDICES,
    RADAR_INDICES,
    RGB_COMPOSITES,
    get_expression,
    get_all_indices,
)

# Environment configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Create FastAPI app
app = FastAPI(
    title="VivaCampo TiTiler",
    description="COG and Mosaic Tile Server for VivaCampo - Dynamic vegetation index rendering",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
add_exception_handlers(app, DEFAULT_STATUS_CODES)

# Configure boto3 for LocalStack (used by cogeo-mosaic)
if AWS_ENDPOINT_URL:
    import boto3

    boto3.setup_default_session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=AWS_REGION,
    )


# Custom dependency to handle Planetary Computer URL signing
def planetary_computer_url_signer(url: str) -> str:
    """Sign URLs from Planetary Computer for authenticated access."""
    parsed = urlparse(url)

    # Check if URL is from Planetary Computer blob storage
    if "blob.core.windows.net" in parsed.netloc:
        try:
            return planetary_computer.sign(url)
        except Exception:
            # If signing fails, return original URL
            pass

    return url


# Custom dependency that signs PC URLs
def SignedDatasetPathParams(
    url: Annotated[str, Query(description="Dataset URL")]
) -> str:
    """Dataset path dependency with Planetary Computer signing."""
    return planetary_computer_url_signer(url)


# COG Tiler (existing functionality)
cog_tiler = TilerFactory(
    router_prefix="/cog",
    path_dependency=SignedDatasetPathParams,
)
app.include_router(cog_tiler.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])

# Mosaic Tiler (new functionality for MosaicJSON)
mosaic_tiler = MosaicTilerFactory(
    router_prefix="/mosaic",
    path_dependency=SignedDatasetPathParams,
)
app.include_router(mosaic_tiler.router, prefix="/mosaic", tags=["MosaicJSON"])


# Health and info endpoints
@app.get("/", tags=["Info"])
def root():
    """Service information."""
    return {
        "service": "VivaCampo TiTiler",
        "version": "2.0.0",
        "description": "Dynamic tile server with MosaicJSON support",
        "endpoints": {
            "cog": {
                "tiles": "/cog/tiles/{z}/{x}/{y}",
                "info": "/cog/info",
                "statistics": "/cog/statistics",
                "preview": "/cog/preview",
            },
            "mosaic": {
                "tiles": "/mosaic/tiles/{z}/{x}/{y}",
                "info": "/mosaic/info",
                "statistics": "/mosaic/statistics",
            },
            "indices": "/indices",
            "health": "/health",
        },
    }


@app.get("/health", tags=["Info"])
def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/indices", tags=["Info"])
def list_indices():
    """List all available vegetation indices with their expressions."""
    return {
        "vegetation": {
            name: {
                "name": config["name"],
                "description": config["description"],
                "expression": config["expression"],
                "colormap": config["colormap"],
                "rescale": config["rescale"],
                "bands": config["bands"],
            }
            for name, config in VEGETATION_INDICES.items()
        },
        "radar": {
            name: {
                "name": config["name"],
                "description": config["description"],
                "expression": config["expression"],
                "colormap": config["colormap"],
                "rescale": config["rescale"],
                "bands": config["bands"],
            }
            for name, config in RADAR_INDICES.items()
        },
        "rgb_composites": {
            name: {
                "name": config["name"],
                "description": config["description"],
                "bands": config["bands"],
            }
            for name, config in RGB_COMPOSITES.items()
        },
    }


@app.get("/indices/{index_name}", tags=["Info"])
def get_index_info(index_name: str):
    """Get information about a specific index."""
    expr = get_expression(index_name)
    if not expr:
        raise HTTPException(
            status_code=404,
            detail=f"Index '{index_name}' not found. Use /indices to list available indices.",
        )
    return {
        "index": index_name,
        **expr,
        "usage": {
            "cog": f"/cog/tiles/{{z}}/{{x}}/{{y}}.png?url={{cog_url}}&expression={expr['expression']}&colormap_name={expr['colormap']}&rescale={expr['rescale']}",
            "mosaic": f"/mosaic/tiles/{{z}}/{{x}}/{{y}}.png?url={{mosaic_url}}&expression={expr['expression']}&colormap_name={expr['colormap']}&rescale={expr['rescale']}",
        },
    }


# Convenience endpoint for index tiles
@app.get(
    "/index/{index_name}/tiles/{z}/{x}/{y}.png",
    tags=["Convenience"],
    response_class=Response,
)
async def get_index_tile(
    request: Request,
    index_name: str,
    z: int,
    x: int,
    y: int,
    url: Annotated[str, Query(description="COG or MosaicJSON URL")],
    source: Annotated[
        Literal["cog", "mosaic"], Query(description="Data source type")
    ] = "mosaic",
):
    """
    Convenience endpoint for fetching pre-configured index tiles.

    Example:
        /index/ndvi/tiles/13/2847/4523.png?url=s3://bucket/mosaic.json&source=mosaic
    """
    expr = get_expression(index_name)
    if not expr:
        raise HTTPException(
            status_code=404,
            detail=f"Index '{index_name}' not found.",
        )

    # Build redirect URL to appropriate tiler
    signed_url = planetary_computer_url_signer(url)
    base_path = f"/{source}/tiles/{z}/{x}/{y}.png"

    # Construct query params
    params = {
        "url": signed_url,
        "expression": expr["expression"],
        "colormap_name": expr["colormap"],
        "rescale": expr["rescale"],
    }

    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    redirect_url = f"{base_path}?{query_string}"

    # Forward to internal route
    from starlette.responses import RedirectResponse

    return RedirectResponse(url=redirect_url, status_code=307)


# STAC Item Tile Endpoint - for multi-band vegetation indices
@app.get(
    "/stac/tiles/{z}/{x}/{y}.png",
    tags=["STAC"],
    response_class=Response,
)
async def get_stac_tile(
    z: int,
    x: int,
    y: int,
    url: Annotated[str, Query(description="STAC Item URL")],
    expression: Annotated[str, Query(description="Band math expression (e.g., '(B08-B04)/(B08+B04)')")] = None,
    assets: Annotated[str, Query(description="Comma-separated list of assets to use")] = None,
    colormap_name: Annotated[str, Query(description="Colormap name")] = None,
    rescale: Annotated[str, Query(description="Rescale values (e.g., '-0.2,0.8')")] = None,
):
    """
    Render a tile from a STAC Item with multi-band expression support.

    This endpoint supports vegetation indices that require multiple bands
    from Sentinel-2 data (e.g., NDVI needs B04 and B08).

    Example:
        /stac/tiles/14/5920/8520.png?url=<stac_item_url>&expression=(B08-B04)/(B08+B04)&colormap_name=rdylgn&rescale=-0.2,0.8
    """
    from rio_tiler.io.stac import STACReader
    from rio_tiler.colormap import cmap
    from rio_tiler.utils import render
    import numpy as np

    # Sign URL if from Planetary Computer
    signed_url = planetary_computer_url_signer(url)

    try:
        with STACReader(signed_url) as stac:
            # Determine which assets to read
            if expression:
                # Parse expression to find required bands
                import re
                band_pattern = r'B\d{2}[A]?'
                required_bands = list(set(re.findall(band_pattern, expression)))

                if not required_bands:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Could not parse bands from expression: {expression}"
                    )

                # Read tile data with required bands
                # asset_as_band=True allows using asset names as band names in expressions
                img = stac.tile(
                    x, y, z,
                    assets=required_bands,
                    expression=expression,
                    asset_as_band=True
                )

            elif assets:
                # Use specified assets
                asset_list = assets.split(",")
                img = stac.tile(x, y, z, assets=asset_list, asset_as_band=True)
            else:
                # Default to visual composite
                if "visual" in stac.assets:
                    img = stac.tile(x, y, z, assets=["visual"])
                else:
                    # Fallback to RGB bands
                    img = stac.tile(x, y, z, assets=["B04", "B03", "B02"], asset_as_band=True)

            # Apply colormap if specified
            if colormap_name and expression:
                colormap_obj = cmap.get(colormap_name)

                # Rescale if specified
                if rescale:
                    vmin, vmax = map(float, rescale.split(","))
                    data = img.data[0]  # First band from expression result
                    data = np.clip((data - vmin) / (vmax - vmin), 0, 1)
                    data = (data * 255).astype(np.uint8)

                    # Apply colormap
                    content = render(
                        data.reshape(1, *data.shape),
                        img.mask,
                        colormap=colormap_obj,
                    )
                else:
                    content = render(
                        img.data,
                        img.mask,
                        colormap=colormap_obj,
                    )
            else:
                # Render without colormap
                content = render(img.data, img.mask)

            return Response(content=content, media_type="image/png")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading STAC item: {str(e)}"
        )


# STAC-based Mosaic Tile Endpoint - reads STAC items from MosaicJSON
@app.get(
    "/stac-mosaic/tiles/{z}/{x}/{y}.png",
    tags=["STAC"],
    response_class=Response,
)
async def get_stac_mosaic_tile(
    z: int,
    x: int,
    y: int,
    url: Annotated[str, Query(description="MosaicJSON URL with STAC item references")],
    expression: Annotated[str, Query(description="Band math expression")] = None,
    colormap_name: Annotated[str, Query(description="Colormap name")] = "rdylgn",
    rescale: Annotated[str, Query(description="Rescale values")] = "-0.2,0.8",
):
    """
    Render a tile from a MosaicJSON containing STAC Item URLs.

    The MosaicJSON should contain STAC item URLs (not COG URLs) in its tiles.
    This endpoint will read the first matching STAC item and compute the
    vegetation index using multiple bands.

    Example:
        /stac-mosaic/tiles/14/5920/8520.png?url=s3://bucket/mosaic-stac.json&expression=(B08-B04)/(B08+B04)
    """
    from cogeo_mosaic.backends import MosaicBackend
    from rio_tiler.io.stac import STACReader
    from rio_tiler.colormap import cmap
    from rio_tiler.utils import render
    import numpy as np
    import re

    try:
        # Get assets (STAC item URLs) for this tile from the mosaic
        with MosaicBackend(url) as mosaic:
            stac_urls = mosaic.assets_for_tile(x, y, z)

        if not stac_urls:
            # Return transparent tile if no data
            return Response(
                content=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x06\x00\x00\x00\x5c\x72\xa8f\x00\x00\x00\x00IEND\xaeB`\x82',
                media_type="image/png"
            )

        # Get the first STAC item URL (may be pre-signed or unsigned)
        stac_url = stac_urls[0]

        # If it's a Planetary Computer STAC API URL, fetch and sign it
        if "planetarycomputer.microsoft.com/api/stac" in stac_url:
            # This is a STAC item URL - sign it fresh at request time
            stac_url = planetary_computer.sign(stac_url)
        elif "blob.core.windows.net" in stac_url:
            # This is a COG URL that needs signing
            stac_url = planetary_computer_url_signer(stac_url)

        # Read tile from STAC item
        # asset_as_band=True allows using asset names as band names in expressions
        # Use planetary_computer.sign_inplace to sign asset URLs on access
        import pystac

        # Fetch the STAC item
        stac_item = pystac.Item.from_file(stac_url)
        # Sign all asset URLs in place
        stac_item = planetary_computer.sign_inplace(stac_item)

        with STACReader(None, item=stac_item) as stac:
            if expression:
                # Parse bands from expression
                band_pattern = r'B\d{2}[A]?'
                required_bands = list(set(re.findall(band_pattern, expression)))

                if not required_bands:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Could not parse bands from expression: {expression}"
                    )

                # Read tile with expression - asset_as_band treats each asset as a band
                img = stac.tile(
                    x, y, z,
                    assets=required_bands,
                    expression=expression,
                    asset_as_band=True
                )
            else:
                # Default RGB from visual or RGB bands
                if "visual" in stac.assets:
                    img = stac.tile(x, y, z, assets=["visual"])
                else:
                    img = stac.tile(x, y, z, assets=["B04", "B03", "B02"], asset_as_band=True)

            # Apply colormap and rescale
            if colormap_name and expression:
                colormap_obj = cmap.get(colormap_name)

                if rescale:
                    vmin, vmax = map(float, rescale.split(","))
                    data = img.data[0]
                    data = np.clip((data - vmin) / (vmax - vmin), 0, 1)
                    data = (data * 255).astype(np.uint8)
                    content = render(
                        data.reshape(1, *data.shape),
                        img.mask,
                        colormap=colormap_obj,
                    )
                else:
                    content = render(img.data, img.mask, colormap=colormap_obj)
            else:
                content = render(img.data, img.mask)

            return Response(content=content, media_type="image/png")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading STAC mosaic: {str(e)}"
        )


# Middleware to add cache headers
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    """Add cache headers to tile responses."""
    response = await call_next(request)

    # Add cache headers for tile endpoints
    if "/tiles/" in request.url.path and response.status_code == 200:
        # Cache tiles for 7 days (they don't change once generated)
        response.headers["Cache-Control"] = "public, max-age=604800, immutable"
        response.headers["Vary"] = "Accept-Encoding"

    return response


# Error handler for Planetary Computer issues
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions with helpful messages."""
    error_msg = str(exc)

    # Check for common PC issues
    if "403" in error_msg or "Forbidden" in error_msg:
        return JSONResponse(
            status_code=403,
            content={
                "error": "Access denied",
                "detail": "URL may need signing. Ensure Planetary Computer URLs are properly signed.",
                "hint": "The server attempts to sign PC URLs automatically. Check if the URL format is correct.",
            },
        )

    if "404" in error_msg or "Not Found" in error_msg:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Resource not found",
                "detail": error_msg,
            },
        )

    # Generic error
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": error_msg,
        },
    )
