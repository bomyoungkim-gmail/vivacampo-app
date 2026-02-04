# FEAT-0008 — GIS Integration (QGIS/ArcGIS)

Date: 2026-02-04
Status: Done

## Goal
Enable professional GIS users to integrate VivaCampo tile layers into QGIS and ArcGIS for advanced spatial analysis, overlaying with proprietary data, and custom map production.

## User Stories
- As a GIS analyst, I want to add VivaCampo vegetation index layers to QGIS, so that I can overlay them with my field boundaries and soil data.
- As an agronomist, I want to view historical NDVI trends in ArcGIS Pro, so that I can create professional reports for clients.
- As a farm manager, I want to export VivaCampo data to my existing GIS workflow, so that I maintain a single source of truth for spatial data.

## Contract Changes
- API: `GET /api/v1/tiles/{tenant_id}/{aoi_id}/tilejson.json` returns TileJSON 3.0 spec
- API: `GET /api/v1/tiles/config` returns CDN URL and supported indices
- Data: No changes (uses existing MosaicJSON + TiTiler infrastructure)

## Technical Details

### TileJSON Endpoint

The API exposes a TileJSON 3.0 compatible endpoint that can be consumed by any GIS application:

```
GET /api/v1/tiles/{tenant_id}/{aoi_id}/tilejson.json?index=ndvi&year=2026&week=5
```

Response:
```json
{
  "tilejson": "3.0.0",
  "name": "VivaCampo NDVI",
  "tiles": [
    "https://tiles.vivacampo.com.br/api/v1/tiles/{tenant_id}/{aoi_id}/{z}/{x}/{y}.png?index=ndvi&year=2026&week=5"
  ],
  "minzoom": 8,
  "maxzoom": 18,
  "bounds": [-52.5, -23.5, -52.0, -23.0],
  "center": [-52.25, -23.25, 14]
}
```

### Supported Vegetation Indices

| Index | Expression | Use Case |
|-------|------------|----------|
| `ndvi` | (B08-B04)/(B08+B04) | Overall vegetation health |
| `ndre` | (B08-B05)/(B08+B05) | Chlorophyll content, nitrogen stress |
| `ndwi` | (B03-B08)/(B03+B08) | Water content in vegetation |
| `ndmi` | (B08-B11)/(B08+B11) | Moisture stress detection |
| `evi` | 2.5*(B08-B04)/(B08+6*B04-7.5*B02+1) | Enhanced vegetation (reduces soil background) |
| `savi` | 1.5*(B08-B04)/(B08+B04+0.5) | Soil-adjusted vegetation |
| `gndvi` | (B08-B03)/(B08+B03) | Green NDVI (canopy chlorophyll) |

## QGIS Integration

### Method 1: Add XYZ Tiles Layer

1. Open QGIS
2. Go to **Layer** → **Add Layer** → **Add XYZ Tiles Layer**
3. Click **New** to create a new connection
4. Configure:
   - **Name**: `VivaCampo NDVI`
   - **URL**: `https://tiles.vivacampo.com.br/api/v1/tiles/{tenant_id}/{aoi_id}/{z}/{x}/{y}.png?index=ndvi&year=2026&week=5`
   - **Min Zoom**: 8
   - **Max Zoom**: 18
5. Click **OK** and **Add**

### Method 2: Using TileJSON (Recommended)

1. Install the **TileJSON Loader** plugin from QGIS Plugin Manager
2. Go to **Plugins** → **TileJSON Loader** → **Load TileJSON**
3. Enter the TileJSON URL:
   ```
   https://api.vivacampo.com.br/api/v1/tiles/{tenant_id}/{aoi_id}/tilejson.json?index=ndvi&year=2026&week=5
   ```
4. Add authentication header (Bearer token) in the request settings
5. Click **Load**

### Method 3: Python Console

```python
from qgis.core import QgsRasterLayer, QgsProject

# Configure tile URL
tenant_id = "your-tenant-uuid"
aoi_id = "your-aoi-uuid"
index = "ndvi"
year = 2026
week = 5

# Create XYZ tile layer
url = f"type=xyz&url=https://tiles.vivacampo.com.br/api/v1/tiles/{tenant_id}/{aoi_id}/{{z}}/{{x}}/{{y}}.png?index={index}%26year={year}%26week={week}"
layer = QgsRasterLayer(url, f"VivaCampo {index.upper()} W{week}", "wms")

if layer.isValid():
    QgsProject.instance().addMapLayer(layer)
else:
    print("Failed to load layer")
```

### Authentication in QGIS

For authenticated requests, configure a network interceptor:

1. Go to **Settings** → **Options** → **Network**
2. Under **HTTP Headers**, add:
   - **Header**: `Authorization`
   - **Value**: `Bearer <your-jwt-token>`

Or use the QGIS Authentication Manager:
1. Go to **Settings** → **Options** → **Authentication**
2. Create a new authentication config with your JWT token

## ArcGIS Pro Integration

### Method 1: Add WMTS/TileLayer

1. Open ArcGIS Pro
2. Go to **Insert** → **Connections** → **New WMTS Server**
3. Enter the TileJSON URL (ArcGIS parses TileJSON format)
4. Add authentication if required

### Method 2: Using ArcPy

```python
import arcpy

# Configure tile URL
tenant_id = "your-tenant-uuid"
aoi_id = "your-aoi-uuid"
index = "ndvi"
year = 2026
week = 5

# Create tile layer
tile_url = f"https://tiles.vivacampo.com.br/api/v1/tiles/{tenant_id}/{aoi_id}/{{z}}/{{x}}/{{y}}.png?index={index}&year={year}&week={week}"

# Add as web tile layer
arcpy.management.AddWebTileLayer(tile_url, f"VivaCampo_{index.upper()}_W{week}")
```

### Method 3: Tile Package Export

For offline use or sharing, export to TPK format:

1. Add the VivaCampo layer as described above
2. Right-click layer → **Sharing** → **Create Tile Package**
3. Configure zoom levels and extent
4. Export as `.tpk` file

## ArcGIS Online / Portal

### Add as Web Layer

1. Go to **Content** → **Add Item** → **From URL**
2. Select **Tile Layer**
3. Enter URL:
   ```
   https://tiles.vivacampo.com.br/api/v1/tiles/{tenant_id}/{aoi_id}/{z}/{x}/{y}.png?index=ndvi&year=2026&week=5
   ```
4. Configure layer properties

### Create Web Map

1. Open **Map Viewer**
2. Click **Add** → **Add layer from URL**
3. Select **A tile layer**
4. Paste the tile URL

## Authentication

All VivaCampo tile endpoints require authentication via JWT Bearer token.

### Getting a Token

```bash
# Using the CLI
vivacampo auth login

# Or via API
curl -X POST https://api.vivacampo.com.br/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "..."}'
```

### Token Expiration

- Tokens expire after 2 hours by default
- For long-running GIS sessions, use refresh tokens
- Consider using service accounts for automated workflows

## Caching Considerations

### CDN Caching
- Tiles are cached at the CDN edge for 7 days
- Historical tiles (past weeks) are immutable and cache indefinitely
- Current week tiles may update as new satellite imagery arrives

### Local Caching
- QGIS: Enable tile caching in **Settings** → **Options** → **Network**
- ArcGIS: Configure cache in **Options** → **Display** → **Cache**

### Cache Invalidation
When requesting tiles for the current week, add a cache-buster parameter:
```
?index=ndvi&year=2026&week=5&t={unix_timestamp}
```

## Troubleshooting

### Tiles Not Loading

1. **Check authentication**: Verify JWT token is valid and not expired
2. **Check zoom level**: Tiles only available between zoom 8-18
3. **Check AOI permissions**: User must have access to the AOI
4. **Network issues**: Verify firewall allows HTTPS to tiles.vivacampo.com.br

### Blank or Black Tiles

1. **No data available**: Check if imagery exists for the requested week
2. **Cloud cover**: High cloud cover may result in NO_DATA status
3. **AOI outside coverage**: Verify AOI is within Sentinel-2 coverage area

### Slow Performance

1. Enable local tile caching
2. Use CDN URLs instead of direct API
3. Limit zoom levels when adding layers

## Acceptance Criteria
- [x] TileJSON endpoint returns valid TileJSON 3.0 spec
- [x] Tiles load correctly in QGIS via XYZ connection
- [x] Tiles load correctly in ArcGIS Pro
- [x] Authentication works with Bearer tokens
- [x] CDN caching provides sub-200ms response times
- [x] Documentation covers all major GIS platforms
