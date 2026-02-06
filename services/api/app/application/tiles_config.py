"""Shared tile configuration and helpers."""
from __future__ import annotations

from datetime import date
from urllib.parse import quote

from app.config import settings

# TiTiler internal URL
TILER_URL = getattr(settings, "tiler_url", "http://tiler:8080")

# Vegetation index expressions (must match TiTiler expressions.py)
# NOTE: Current MosaicJSON uses "visual" composite (RGB) which only supports
# true_color display. For vegetation indices, TiTiler-STAC endpoint resolves
# individual band COGs for expression computation.
EXPRESSIONS = {
    "ndvi": "(B08-B04)/(B08+B04)",
    "ndwi": "(B03-B08)/(B03+B08)",
    "ndmi": "(B08-B11)/(B08+B11)",
    "evi": "2.5*(B08-B04)/(B08+6*B04-7.5*B02+1)",
    "savi": "1.5*(B08-B04)/(B08+B04+0.5)",
    "ndre": "(B08-B05)/(B08+B05)",
    "gndvi": "(B08-B03)/(B08+B03)",
    "true_color": None,
}

COLORMAPS = {
    "ndvi": "rdylgn",
    "ndwi": "blues",
    "ndmi": "blues",
    "evi": "rdylgn",
    "savi": "rdylgn",
    "ndre": "rdylgn",
    "gndvi": "rdylgn",
    "true_color": None,
}

RESCALES = {
    "ndvi": "-0.2,0.8",
    "ndwi": "-0.5,0.5",
    "ndmi": "-0.5,0.5",
    "evi": "-0.2,0.8",
    "savi": "-0.2,0.8",
    "ndre": "-0.2,0.8",
    "gndvi": "-0.2,0.8",
    "true_color": None,
}


def get_current_iso_week() -> tuple[int, int]:
    today = date.today()
    iso_cal = today.isocalendar()
    return iso_cal.year, iso_cal.week


def get_mosaic_url(year: int, week: int, collection: str = "sentinel-2-l2a") -> str:
    return f"s3://{settings.s3_bucket}/mosaics/{collection}/{year}/w{week:02d}.json"


def build_tiler_url(z: int, x: int, y: int, index: str, year: int, week: int) -> str:
    mosaic_url = get_mosaic_url(year, week)
    expression = EXPRESSIONS.get(index)
    colormap = COLORMAPS.get(index)
    rescale = RESCALES.get(index)

    if expression:
        tiler_url = (
            f"{TILER_URL}/stac-mosaic/tiles/{z}/{x}/{y}.png"
            f"?url={quote(mosaic_url, safe='')}"
            f"&expression={quote(expression, safe='')}"
        )
        if colormap:
            tiler_url += f"&colormap_name={colormap}"
        if rescale:
            tiler_url += f"&rescale={rescale}"
        return tiler_url

    return (
        f"{TILER_URL}/mosaic/tiles/WebMercatorQuad/{z}/{x}/{y}.png"
        f"?url={quote(mosaic_url, safe='')}"
    )
