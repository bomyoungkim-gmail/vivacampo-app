"""
Vegetation indices expressions for TiTiler.

These expressions are used with TiTiler's expression parameter to calculate
vegetation indices on-the-fly from Sentinel-2 bands.

Band mapping (Sentinel-2 L2A):
- B02: Blue (10m)
- B03: Green (10m)
- B04: Red (10m)
- B05: Red Edge 1 (20m)
- B06: Red Edge 2 (20m)
- B07: Red Edge 3 (20m)
- B08: NIR (10m)
- B8A: NIR Narrow (20m)
- B11: SWIR 1 (20m)
- B12: SWIR 2 (20m)
"""

# Vegetation Indices - Expressions for TiTiler
VEGETATION_INDICES = {
    # Basic vegetation indices
    "ndvi": {
        "expression": "(B08-B04)/(B08+B04)",
        "name": "Normalized Difference Vegetation Index",
        "description": "Measures vegetation health and density",
        "rescale": "-0.2,0.8",
        "colormap": "rdylgn",
        "bands": ["B04", "B08"],
    },
    "ndwi": {
        "expression": "(B03-B08)/(B03+B08)",
        "name": "Normalized Difference Water Index",
        "description": "Detects water content in vegetation",
        "rescale": "-0.5,0.5",
        "colormap": "blues",
        "bands": ["B03", "B08"],
    },
    "ndmi": {
        "expression": "(B08-B11)/(B08+B11)",
        "name": "Normalized Difference Moisture Index",
        "description": "Measures vegetation water content",
        "rescale": "-0.5,0.5",
        "colormap": "blues",
        "bands": ["B08", "B11"],
    },
    "evi": {
        "expression": "2.5*(B08-B04)/(B08+6*B04-7.5*B02+1)",
        "name": "Enhanced Vegetation Index",
        "description": "Enhanced vegetation monitoring, reduces atmospheric effects",
        "rescale": "-0.2,0.8",
        "colormap": "rdylgn",
        "bands": ["B02", "B04", "B08"],
    },
    "savi": {
        "expression": "1.5*(B08-B04)/(B08+B04+0.5)",
        "name": "Soil Adjusted Vegetation Index",
        "description": "Minimizes soil brightness influences",
        "rescale": "-0.2,0.8",
        "colormap": "rdylgn",
        "bands": ["B04", "B08"],
    },

    # Red Edge indices (better for crop monitoring)
    "ndre": {
        "expression": "(B08-B05)/(B08+B05)",
        "name": "Normalized Difference Red Edge",
        "description": "Sensitive to chlorophyll content, good for crop monitoring",
        "rescale": "-0.2,0.8",
        "colormap": "rdylgn",
        "bands": ["B05", "B08"],
    },
    "reci": {
        "expression": "(B08/B05)-1",
        "name": "Red Edge Chlorophyll Index",
        "description": "Estimates chlorophyll content in leaves",
        "rescale": "0,3",
        "colormap": "viridis",
        "bands": ["B05", "B08"],
    },
    "srre": {
        "expression": "B08/B05",
        "name": "Simple Ratio Red Edge",
        "description": "Nitrogen absorption indicator (R² > 0.8 for corn/rice)",
        "rescale": "0.5,8",
        "colormap": "rdylgn",
        "bands": ["B05", "B08"],
    },
    "gndvi": {
        "expression": "(B08-B03)/(B08+B03)",
        "name": "Green Normalized Difference Vegetation Index",
        "description": "More sensitive to chlorophyll concentration",
        "rescale": "-0.2,0.8",
        "colormap": "rdylgn",
        "bands": ["B03", "B08"],
    },

    # Stress and damage indices
    "msi": {
        "expression": "B11/B08",
        "name": "Moisture Stress Index",
        "description": "Detects water stress in vegetation",
        "rescale": "0,2",
        "colormap": "rdylbu_r",
        "bands": ["B08", "B11"],
    },
    "nbr": {
        "expression": "(B08-B12)/(B08+B12)",
        "name": "Normalized Burn Ratio",
        "description": "Identifies burned areas and fire severity",
        "rescale": "-0.5,0.5",
        "colormap": "rdylgn",
        "bands": ["B08", "B12"],
    },
    "bsi": {
        "expression": "((B11+B04)-(B08+B02))/((B11+B04)+(B08+B02))",
        "name": "Bare Soil Index",
        "description": "Identifies bare soil areas",
        "rescale": "-0.5,0.5",
        "colormap": "reds",
        "bands": ["B02", "B04", "B08", "B11"],
    },

    # Pigment indices
    "ari": {
        "expression": "(1/B03)-(1/B05)",
        "name": "Anthocyanin Reflectance Index",
        "description": "Detects anthocyanin pigments (stress indicator)",
        "rescale": "0,0.1",
        "colormap": "plasma",
        "bands": ["B03", "B05"],
    },
    "cri": {
        "expression": "(1/B02)-(1/B03)",
        "name": "Carotenoid Reflectance Index",
        "description": "Estimates carotenoid content",
        "rescale": "0,0.1",
        "colormap": "plasma",
        "bands": ["B02", "B03"],
    },

    # Simple ratio
    "rvi": {
        "expression": "B08/B04",
        "name": "Ratio Vegetation Index",
        "description": "Simple NIR/Red ratio for vegetation",
        "rescale": "0,10",
        "colormap": "rdylgn",
        "bands": ["B04", "B08"],
    },
}

# Radar indices (Sentinel-1)
RADAR_INDICES = {
    "rvi_radar": {
        "expression": "4*VH/(VV+VH)",
        "name": "Radar Vegetation Index",
        "description": "Vegetation monitoring using radar (all-weather)",
        "rescale": "0,1.5",
        "colormap": "viridis",
        "bands": ["VV", "VH"],
    },
    "ratio": {
        "expression": "VH/VV",
        "name": "VH/VV Ratio",
        "description": "Cross-polarization ratio",
        "rescale": "0,0.5",
        "colormap": "viridis",
        "bands": ["VV", "VH"],
    },
}

# RGB composites for visualization
RGB_COMPOSITES = {
    "true_color": {
        "bands": ["B04", "B03", "B02"],
        "name": "True Color",
        "description": "Natural colors as seen by human eye",
        "rescale": "0,3000",
    },
    "false_color": {
        "bands": ["B08", "B04", "B03"],
        "name": "False Color (Vegetation)",
        "description": "NIR-Red-Green composite, vegetation appears red",
        "rescale": "0,5000",
    },
    "agriculture": {
        "bands": ["B11", "B08", "B02"],
        "name": "Agriculture",
        "description": "SWIR-NIR-Blue composite for crop monitoring",
        "rescale": "0,5000",
    },
    "moisture": {
        "bands": ["B8A", "B11", "B12"],
        "name": "Moisture",
        "description": "Highlights moisture content",
        "rescale": "0,5000",
    },
}


def get_expression(index_name: str) -> dict | None:
    """Get expression configuration for an index."""
    index_name = index_name.lower()
    if index_name in VEGETATION_INDICES:
        return VEGETATION_INDICES[index_name]
    if index_name in RADAR_INDICES:
        return RADAR_INDICES[index_name]
    return None


def get_all_indices() -> dict:
    """Get all available indices."""
    return {**VEGETATION_INDICES, **RADAR_INDICES}


def get_colormap(index_name: str) -> str:
    """Get default colormap for an index."""
    expr = get_expression(index_name)
    return expr["colormap"] if expr else "viridis"


def get_rescale(index_name: str) -> str:
    """Get default rescale values for an index."""
    expr = get_expression(index_name)
    return expr["rescale"] if expr else "-1,1"
