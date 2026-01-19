"""
Real STAC client for fetching satellite imagery.
Integrates with Microsoft Planetary Computer and other STAC catalogs.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from pystac_client import Client
from shapely.geometry import shape, mapping
import rasterio
from rasterio.mask import mask
import numpy as np
import asyncio


logger = structlog.get_logger()


class STACClient:
    """
    STAC client for fetching Sentinel-2 imagery.
    Uses Microsoft Planetary Computer by default.
    """
    
    def __init__(self, catalog_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1"):
        self.catalog_url = catalog_url
        self.client = None
    
    def _get_client(self):
        """Lazy initialization of STAC client"""
        if self.client is None:
            try:
                self.client = Client.open(self.catalog_url)
                logger.info("stac_client_initialized", catalog=self.catalog_url)
            except Exception as e:
                logger.error("stac_client_init_failed", exc_info=e)
                raise
        return self.client
    
    async def search_scenes(
        self,
        aoi_geom: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 60.0,
        collections: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for satellite scenes covering the AOI.
        
        Args:
            aoi_geom: GeoJSON geometry (MultiPolygon)
            start_date: Start of date range
            end_date: End of date range
            max_cloud_cover: Maximum cloud cover percentage (0-100)
            collections: STAC collections to search (default: Sentinel-2 L2A)
        
        Returns:
            List of scene metadata
        """
        if collections is None:
            collections = ["sentinel-2-l2a"]
        
        try:
            client = self._get_client()
            
            # Search STAC catalog
            search = client.search(
                collections=collections,
                intersects=aoi_geom,
                datetime=f"{start_date.isoformat()}/{end_date.isoformat()}",
                query={
                    "eo:cloud_cover": {"lt": max_cloud_cover}
                },
                max_items=100
            )
            
            items = list(search.items())
            
            logger.info("stac_search_completed",
                       scenes_found=len(items),
                       start_date=str(start_date),
                       end_date=str(end_date))
            
            # Convert to simplified metadata
            scenes = []
            for item in items:
                # Asset mapping based on collection
                assets = {}
                collection_id = item.collection_id
                
                if "sentinel-2" in collection_id:
                    assets = {
                        "red": item.assets.get("B04").href if "B04" in item.assets else None,
                        "green": item.assets.get("B03").href if "B03" in item.assets else None,
                        "blue": item.assets.get("B02").href if "B02" in item.assets else None,
                        "nir": item.assets.get("B08").href if "B08" in item.assets else None,
                        "swir": item.assets.get("B11").href if "B11" in item.assets else None,
                        "scl": item.assets.get("SCL").href if "SCL" in item.assets else None,
                    }
                elif "copernicus-dem" in collection_id:
                     assets = {
                        "dem": item.assets.get("data").href if "data" in item.assets else None
                     }

                elif "sentinel-1" in collection_id:
                    # Sentinel-1 RTC/GRD usually has 'vv' and 'vh'
                    assets = {
                        "vv": item.assets.get("vv").href if "vv" in item.assets else None,
                        "vh": item.assets.get("vh").href if "vh" in item.assets else None,
                    }
                
                scenes.append({
                    "id": item.id,
                    "datetime": item.datetime.isoformat(),
                    "cloud_cover": item.properties.get("eo:cloud_cover", 0), # S1 usually 0 or null
                    "platform": item.properties.get("platform", "unknown"),
                    "assets": assets,
                    "bbox": item.bbox,
                    "geometry": mapping(shape(item.geometry))
                })
            
            return scenes
        
        except Exception as e:
            logger.error("stac_search_failed", exc_info=e)
            raise
    
    def _download_asset(self, href: str) -> str:
        """
        Download asset using standard library urllib for maximum stability
        in containerized environments where requests/OpenSSL might hang.
        """
        import urllib.request
        import tempfile
        import os
        import time
        import random
        import socket
        
        # Sign URL (Planetary Computer assets need SAS tokens)
        import planetary_computer
        try:
            signed_href = planetary_computer.sign(href)
            logger.info("signing_debug", original=href[:50], signed=True)
        except Exception as e:
            logger.warning("signing_failed_fallback", exc_info=e)
            signed_href = href

        max_attempts = 5
        
        for attempt in range(max_attempts):
            try:
                # Set global socket timeout for this operation
                socket.setdefaulttimeout(30)
                
                logger.info("download_start_urllib", url=signed_href[:50], attempt=attempt+1)
                
                fd, temp_path = tempfile.mkstemp(suffix=".tif")
                os.close(fd)
                
                # Standard library download - simpler network stack
                # Retries are handled by our loop, not the lib
                with urllib.request.urlopen(signed_href) as response:
                    with open(temp_path, 'wb') as f:
                        while True:
                            chunk = response.read(16 * 1024) # 16KB chunks
                            if not chunk:
                                break
                            f.write(chunk)
                            
                size = os.path.getsize(temp_path)
                logger.info("download_completed", temp_path=temp_path, size_bytes=size)
                return temp_path

            except Exception as e:
                logger.error("download_error_urllib", error=str(e))
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise e

    async def download_and_clip_band(
        self,
        asset_href: str,
        aoi_geom: Dict[str, Any],
        output_path: str
    ) -> np.ndarray:
        """
        Download and clip a raster band to AOI.
        Uses local download first to avoid VSI conflicts.
        """
        import os
        local_path = None
        try:
            # 1. Download to temp file
            local_path = await asyncio.to_thread(self._download_asset, asset_href)
            
            # 2. Open local raster and clip
            with rasterio.open(local_path) as src:
                # Reproject AOI to match Raster CRS (crucial for Sentinel-2 UTM)
                from rasterio.warp import transform_geom
                
                # Assuming aoi_geom is EPSG:4326 (GeoJSON standard)
                aoi_projected = transform_geom("EPSG:4326", src.crs, aoi_geom)
                
                geom = [shape(aoi_projected)]
                out_image, out_transform = mask(src, geom, crop=True)
                out_meta = src.meta.copy()
                
                # Update metadata
                out_meta.update({
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform
                })
                
                # Save clipped raster
                with rasterio.open(output_path, "w", **out_meta) as dest:
                    dest.write(out_image)
                
                logger.info("band_clipped", output=output_path)
                
                return out_image[0]  # Return first band
                
        except Exception as e:
            logger.error("band_clip_failed", asset=asset_href, exc_info=e)
            raise
        finally:
            # 3. Cleanup temp file
            if local_path and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except:
                    pass



    
    async def calculate_ndvi(self, red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """Calculate NDVI = (NIR - Red) / (NIR + Red)"""
        denom = nir + red
        denom = np.where(denom == 0, 0.0001, denom)
        ndvi = (nir - red) / denom
        return np.clip(ndvi, -1, 1)

    async def calculate_ndwi(self, green: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """Calculate NDWI = (Green - NIR) / (Green + NIR)"""
        denom = green + nir
        denom = np.where(denom == 0, 0.0001, denom)
        ndwi = (green - nir) / denom
        return np.clip(ndwi, -1, 1)

    async def calculate_ndmi(self, nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
        """Calculate NDMI = (NIR - SWIR) / (NIR + SWIR)"""
        denom = nir + swir
        denom = np.where(denom == 0, 0.0001, denom)
        ndmi = (nir - swir) / denom
        return np.clip(ndmi, -1, 1)

    async def calculate_savi(self, red: np.ndarray, nir: np.ndarray, L: float = 0.5) -> np.ndarray:
        """Calculate SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)"""
        denom = nir + red + L
        denom = np.where(denom == 0, 0.0001, denom)
        savi = ((nir - red) / denom) * (1 + L)
        return np.clip(savi, -1, 1)

    async def calculate_rvi(self, vv: np.ndarray, vh: np.ndarray) -> np.ndarray:
        """
        Calculate RVI (Radar Vegetation Index) = 4 * VH / (VV + VH)
        Range: 0 (bare soil) to 1 (dense vegetation)
        """
        # Ensure we are working with linear power, not dB.
        # Assuming input is linear (RTC usually is). If dB, convert first.
        # Let's assume input is linear for now as per Planetary Computer RTC specs.
        
        numerator = 4 * vh
        denominator = vv + vh
        denominator = np.where(denominator == 0, 0.0001, denominator)
        
        rvi = numerator / denominator
        return np.clip(rvi, 0, 1)

    async def calculate_radar_ratio(self, vv: np.ndarray, vh: np.ndarray) -> np.ndarray:
        """Calculate VH/VV Ratio"""
        vv = np.where(vv == 0, 0.0001, vv)
        return vh / vv

    async def mask_clouds(
        self,
        data_array: np.ndarray,
        scl_array: np.ndarray
    ) -> np.ndarray:
        """
        Mask clouds using Sentinel-2 Scene Classification Layer (SCL).
        
        SCL values:
        - 0: No Data
        - 1: Saturated or defective
        - 2: Dark Area Pixels
        - 3: Cloud Shadows
        - 4: Vegetation
        """
    async def mask_clouds(self, data_array: np.ndarray, scl_array: np.ndarray) -> np.ndarray:
        try:
            logger.error("DEBUG_MASK_CLOUDS_ENTRY", data_shape=data_array.shape, scl_shape=scl_array.shape)
            
            # SCL bands are 20m, others 10m.
            if data_array.shape[-2:] != scl_array.shape[-2:]:
                logger.error("DEBUG_SHAPE_MISMATCH", data_shape=data_array.shape, scl_shape=scl_array.shape)
                
                target_h, target_w = data_array.shape[-2:]
                scl_h, scl_w = scl_array.shape[-2:]

                scale_h = target_h / scl_h
                scale_w = target_w / scl_w

                y_coords = np.arange(target_h) / scale_h
                x_coords = np.arange(target_w) / scale_w

                y_indices = np.round(y_coords).astype(int)
                x_indices = np.round(x_coords).astype(int)

                y_indices = np.clip(y_indices, 0, scl_h - 1)
                x_indices = np.clip(x_indices, 0, scl_w - 1)

                scl_array = scl_array[y_indices[:, None], x_indices]
                logger.error("DEBUG_RESIZED_SCL", new_shape=scl_array.shape)
            
            if data_array.shape[-2:] != scl_array.shape[-2:]:
                 logger.error("CRITICAL_SHAPE_MISMATCH_AFTER_RESIZE", data_shape=data_array.shape, scl_shape=scl_array.shape)
                 raise ValueError(f"Shape mismatch after resize: Data {data_array.shape} vs SCL {scl_array.shape}")

            invalid_pixels = np.isin(scl_array, [0, 1, 3, 8, 9, 10])
            masked_data = np.where(invalid_pixels, np.nan, data_array)
            return masked_data
            
        except Exception as e:
            logger.error("mask_clouds_exception", error=str(e))
            # Re-raise to ensure job fails visibly
            raise e


# Global STAC client instance
_stac_client = None


def get_stac_client() -> STACClient:
    """Get global STAC client instance"""
    global _stac_client
    if _stac_client is None:
        _stac_client = STACClient()
    return _stac_client
