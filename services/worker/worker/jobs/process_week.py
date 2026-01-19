import structlog
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from worker.config import settings
from worker.shared.aws_clients import S3Client
import tempfile
import os
import rasterio
import numpy as np
import asyncio

logger = structlog.get_logger()

# ... (keep handler - will update next)

def export_cog(data: np.ndarray, output_path: str, profile: dict):
    """Export data as Cloud Optimized GeoTIFF"""
    # Create COG-compatible profile
    cog_profile = profile.copy()
    cog_profile.update({
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "compress": "deflate",
        "predictor": 2,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256
    })
    
    with rasterio.open(output_path, 'w', **cog_profile) as dst:
        dst.write(data.astype('float32'), 1)
    
    logger.info("exported_cog", output_path=output_path)


def save_derived_assets(tenant_id: str, aoi_id: str, year: int, week: int, 
                       ndvi_uri: str, anomaly_uri: str, quicklook_uri: str, 
                       ndwi_uri: str, ndmi_uri: str, savi_uri: str, false_color_uri: str, true_color_uri: str,
                       stats: dict,
                       db: Session):
    """Save derived assets to database"""
    from sqlalchemy import text
    
    sql = text("""
        INSERT INTO derived_assets 
        (tenant_id, aoi_id, year, week, pipeline_version, 
         ndvi_s3_uri, anomaly_s3_uri, quicklook_s3_uri,
         ndwi_s3_uri, ndmi_s3_uri, savi_s3_uri, false_color_s3_uri, true_color_s3_uri,
         ndvi_mean, ndvi_min, ndvi_max, ndvi_std,
         ndwi_mean, ndwi_min, ndwi_max, ndwi_std,
         ndmi_mean, ndmi_min, ndmi_max, ndmi_std,
         savi_mean, savi_min, savi_max, savi_std,
         anomaly_mean, anomaly_std)
        VALUES 
        (:tenant_id, :aoi_id, :year, :week, :pipeline_version, 
         :ndvi_uri, :anomaly_uri, :quicklook_uri,
         :ndwi_uri, :ndmi_uri, :savi_uri, :false_color_uri, :true_color_uri,
         :ndvi_mean, :ndvi_min, :ndvi_max, :ndvi_std,
         :ndwi_mean, :ndwi_min, :ndwi_max, :ndwi_std,
         :ndmi_mean, :ndmi_min, :ndmi_max, :ndmi_std,
         :savi_mean, :savi_min, :savi_max, :savi_std,
         :anomaly_mean, :anomaly_std)
        ON CONFLICT (tenant_id, aoi_id, year, week, pipeline_version) DO UPDATE
        SET ndvi_s3_uri = :ndvi_uri, 
            anomaly_s3_uri = :anomaly_uri, 
            quicklook_s3_uri = :quicklook_uri,
            ndwi_s3_uri = :ndwi_uri,
            ndmi_s3_uri = :ndmi_uri,
            savi_s3_uri = :savi_uri,
            false_color_s3_uri = :false_color_uri,
            true_color_s3_uri = :true_color_uri,
            ndvi_mean = :ndvi_mean, ndvi_min = :ndvi_min, ndvi_max = :ndvi_max, ndvi_std = :ndvi_std,
            ndwi_mean = :ndwi_mean, ndwi_min = :ndwi_min, ndwi_max = :ndwi_max, ndwi_std = :ndwi_std,
            ndmi_mean = :ndmi_mean, ndmi_min = :ndmi_min, ndmi_max = :ndmi_max, ndmi_std = :ndmi_std,
            savi_mean = :savi_mean, savi_min = :savi_min, savi_max = :savi_max, savi_std = :savi_std,
            anomaly_mean = :anomaly_mean, anomaly_std = :anomaly_std
    """)
    
    params = {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "year": year,
        "week": week,
        "pipeline_version": settings.pipeline_version,
        "ndvi_uri": ndvi_uri,
        "anomaly_uri": anomaly_uri,
        "quicklook_uri": quicklook_uri,
        "ndwi_uri": ndwi_uri,
        "ndmi_uri": ndmi_uri,
        "savi_uri": savi_uri,
        "false_color_uri": false_color_uri,
        "true_color_uri": true_color_uri
    }
    # Merge stats into params
    params.update(stats)
    
    try:
        logger.info("DEBUG_SAVING_ASSETS_START", tenant=tenant_id, aoi=aoi_id, year=year, week=week)
        db.execute(sql, params)
        db.commit()
        logger.info("DEBUG_SAVING_ASSETS_SUCCESS")
    except Exception as e:
        db.rollback()
        logger.error("DEBUG_SAVING_ASSETS_FAILED", error=str(e), params=str(params))
        raise e


def export_multiband_cog(data: np.ndarray, output_path: str, profile: dict):
    """Export multiband data (Channels, H, W)"""
    cog_profile = profile.copy()
    count = data.shape[0]
    cog_profile.update({
        "driver": "GTiff",
        "dtype": "float32",
        "count": count,
        "compress": "deflate",
        "predictor": 2,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256
    })
    
    # Clip to 0-1 range for visualization if not already
    data = np.clip(data, 0, 1)
    
    with rasterio.open(output_path, 'w', **cog_profile) as dst:
        dst.write(data.astype('float32'))
    logger.info("exported_multiband_cog", output_path=output_path)


def process_week_handler(job_id: str, payload: dict, db: Session):
    """PROCESS_WEEK job handler (Real Implementation)"""
    import asyncio
    logger.info("process_week_start_real", job_id=job_id)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(process_week_async(job_id, payload, db))
        finally:
            loop.close()
    except Exception as e:
        logger.error("process_week_failed_handler", job_id=job_id, exc_info=e)
        update_job_status(job_id, "FAILED", db, error=str(e))

def calculate_band_stats(band_data, prefix):
    """Calculate basic stats for a band"""
    valid_pixels = band_data[~np.isnan(band_data)]
    if valid_pixels.size == 0:
        return {
            f"{prefix}_mean": 0.0,
            f"{prefix}_min": 0.0,
            f"{prefix}_max": 0.0,
            f"{prefix}_std": 0.0
        }
    return {
        f"{prefix}_mean": float(np.nanmean(valid_pixels)),
        f"{prefix}_min": float(np.nanmin(valid_pixels)),
        f"{prefix}_max": float(np.nanmax(valid_pixels)),
        f"{prefix}_std": float(np.nanstd(valid_pixels))
    }

async def process_week_async(job_id: str, payload: dict, db: Session):
    from worker.pipeline.stac_client import get_stac_client
    from worker.shared.utils import get_week_date_range, get_aoi_geometry
    import gc

    tenant_id = payload['tenant_id']
    aoi_id = payload['aoi_id']
    year = payload['year']
    week = payload['week']
    
    # 1. Search
    start_date, end_date = get_week_date_range(year, week)
    aoi_geom = get_aoi_geometry(aoi_id, db)
    client = get_stac_client()
    
    scenes = await client.search_scenes(aoi_geom, start_date, end_date, settings.max_cloud_cover)
    valid_scenes = [s for s in scenes if s['cloud_cover'] <= settings.max_cloud_cover]
    
    is_fallback = False
    
    # Failover / Fallback Logic (Monthly Composite)
    if not valid_scenes:
        logger.info("weekly_search_empty_trying_fallback", year=year, week=week)
        # Expand search to +/- 15 days (approx 1 month)
        fallback_start = start_date - timedelta(days=15)
        fallback_end = end_date + timedelta(days=15)
        
        fallback_scenes = await client.search_scenes(aoi_geom, fallback_start, fallback_end, settings.max_cloud_cover)
        valid_scenes = [s for s in fallback_scenes if s['cloud_cover'] <= settings.max_cloud_cover]
        
        if valid_scenes:
             is_fallback = True
             logger.info("fallback_search_success", count=len(valid_scenes))
    
    if not valid_scenes:
         save_observation_no_data(tenant_id, aoi_id, year, week, db)
         update_job_status(job_id, "DONE", db)
         return
    
    # Pick best scene (lowest cloud cover) - crucial for composite
    best_scene = sorted(valid_scenes, key=lambda s: s['cloud_cover'])[0]
    logger.info("selected_best_scene", scene_id=best_scene['id'], is_fallback=is_fallback)
    
    # helper for reading band from disk
    def load_band(p):
        with rasterio.open(p) as src:
            return src.read(1)

    # 3. Processing (File-based to save RAM)
    with tempfile.TemporaryDirectory() as tmpdir:
        band_paths = {}
        profile = None
        
        # A. Download all to disk (Parallel with Limits)
        logger.info("DEBUG_TRACE: Starting parallel download (Semaphore=2)", job_id=job_id)
        required_bands = ['red', 'green', 'blue', 'nir', 'swir', 'scl']
        
        # Limit concurrency to 2 to prevent OOM/Network starvation
        sem = asyncio.Semaphore(2)

        async def fetch_band(b):
            async with sem:
                href = best_scene['assets'].get(b)
                if not href: 
                    logger.info(f"DEBUG_TRACE: Band {b} has no href", job_id=job_id)
                    return None
                
                p = os.path.join(tmpdir, f"{b}.tif")
                try:
                    logger.info(f"DEBUG_TRACE: Downloading {b}...", job_id=job_id)
                    # Enforce strict 5-minute timeout per band
                    await asyncio.wait_for(
                        client.download_and_clip_band(href, aoi_geom, p),
                        timeout=300.0
                    )
                    logger.info(f"DEBUG_TRACE: Downloaded {b} OK", job_id=job_id)
                    return (b, p)
                except asyncio.TimeoutError:
                    logger.error(f"DEBUG_TRACE: Timeout downloading {b}", job_id=job_id)
                    return None
                except Exception as e:
                    logger.error("DEBUG_TRACE: band_download_failed", band=b, error=str(e), job_id=job_id)
                    return None

        # Fetch all bands concurrently (controlled by semaphore)
        results = await asyncio.gather(*[fetch_band(b) for b in required_bands])
        logger.info("DEBUG_TRACE: Parallel download finished", job_id=job_id)
        
        for res in results:
            if res:
                b, p = res
                band_paths[b] = p
                try:
                    if b == 'red' and profile is None:
                         with rasterio.open(p) as src: profile = src.profile
                except Exception as e:
                    logger.error("DEBUG_TRACE: profile_read_error", band=b, error=str(e), job_id=job_id)

        if 'red' not in band_paths or 'nir' not in band_paths:
            logger.error("DEBUG_TRACE: missing_critical_bands", available=list(band_paths.keys()), job_id=job_id)
            save_observation_no_data(tenant_id, aoi_id, year, week, db)
            update_job_status(job_id, "DONE", db)
            return

        # Force GC after downloads
        gc.collect()

        # B. Mask Clouds (In-place update of files)
        if 'scl' in band_paths:
            scl = load_band(band_paths['scl'])
            
            # Identify valid mask (1=Valid, 0=Cloud)
            # SCL: 0, 1, 3, 8, 9, 10 are bad.
            bad_mask = np.isin(scl, [0, 1, 3, 8, 9, 10])
            del scl # Free SCL array
            
            for b in band_paths:
                if b == 'scl': continue
                
                data = load_band(band_paths[b])
                
                # Check shape mismatch (SCL is 20m, others 10m)
                if data.shape != bad_mask.shape:
                    # Resize mask to data shape (simplistic NN)
                    # Using the previous numpy code for resize:
                    h, w = data.shape
                    hm, wm = bad_mask.shape
                    if h != hm or w != wm:
                        y = (np.arange(h) * (hm / h)).astype(int)
                        x = (np.arange(w) * (wm / w)).astype(int)
                        y = np.clip(y, 0, hm - 1)
                        x = np.clip(x, 0, wm - 1)
                        current_mask = bad_mask[y[:, None], x]
                    else:
                        current_mask = bad_mask
                else:
                    current_mask = bad_mask
                
                # Apply mask
                data = np.where(current_mask, np.nan, data).astype('float32')
                
                # Overwrite file
                with rasterio.open(band_paths[b], 'w', **profile) as dst:
                    dst.write(data, 1)
                
                del data # Early release
                gc.collect()
            
            del bad_mask
            gc.collect()

        # C. Calculate Indices (Load -> Calc -> Save -> Release)
        out_paths = {}
        
        def save_idx(name, arr):
             p = os.path.join(tmpdir, f"{name}.tif")
             export_cog(arr, p, profile)
             out_paths[name] = p
             return arr # Return for chain usage if needed, but mostly we delete

        # NDVI
        red = load_band(band_paths['red'])
        nir = load_band(band_paths['nir'])
        ndvi = await client.calculate_ndvi(red, nir)
        save_idx('ndvi', ndvi)
        
        # Stats needing pixels
        valid_pixels = ndvi[~np.isnan(ndvi)]
        valid_pixel_ratio = len(valid_pixels) / ndvi.size if ndvi.size > 0 else 0
        
        if valid_pixel_ratio < settings.min_valid_pixel_ratio:
              save_observation_no_data(tenant_id, aoi_id, year, week, db)
              update_job_status(job_id, "DONE", db)
              return

        stats = {}
        stats.update(calculate_band_stats(ndvi, "ndvi"))
        
        # Free Red/NIR if not needed? 
        # Needed for SAVI
        savi = await client.calculate_savi(red, nir)
        save_idx('savi', savi)
        stats.update(calculate_band_stats(savi, "savi"))
        del savi
        
        # NDWI (needs Green, NIR)
        del red # Done with Red
        if 'green' in band_paths:
            green = load_band(band_paths['green'])
            ndwi = await client.calculate_ndwi(green, nir)
            save_idx('ndwi', ndwi)
            stats.update(calculate_band_stats(ndwi, "ndwi"))
            del ndwi, green
            
        # NDMI (needs NIR, SWIR)
        if 'swir' in band_paths:
            swir = load_band(band_paths['swir'])
            ndmi = await client.calculate_ndmi(nir, swir)
            save_idx('ndmi', ndmi)
            stats.update(calculate_band_stats(ndmi, "ndmi"))
            del ndmi, swir
        
        del nir # Done with NIR
        gc.collect()

        # Anomaly
        baseline = 0.60
        # Reload NDVI for anomaly (it was deleted? No, we kept variable 'ndvi'?)
        # Wait, 'ndvi' var is still alive.
        anomaly_map = ndvi - baseline
        save_idx('anomaly', anomaly_map)
        stats.update(calculate_band_stats(anomaly_map, "anomaly"))
        
        # Percentiles
        if valid_pixels.size > 0:
            stats['ndvi_p10'] = float(np.nanpercentile(valid_pixels, 10))
            stats['ndvi_p50'] = float(np.nanpercentile(valid_pixels, 50))
            stats['ndvi_p90'] = float(np.nanpercentile(valid_pixels, 90))
        else:
            stats['ndvi_p10'] = 0.0; stats['ndvi_p50'] = 0.0; stats['ndvi_p90'] = 0.0
            
        stats['valid_pixel_ratio'] = valid_pixel_ratio
        del ndvi, valid_pixels, anomaly_map
        gc.collect()
        
        # D. Upload to S3
        s3 = S3Client()
        prefix = f"tenant={tenant_id}/aoi={aoi_id}/year={year}/week={week}/pipeline={settings.pipeline_version}/"
        
        uris = {}
        for k, p in out_paths.items():
            uris[k] = s3.upload_file(p, prefix + f"{k}.tif")

        # Visuals (True/False Color) - complex, skip for now to save memory or implement strictly if requested?
        # User wants "Other corrections". Visualization is nice.
        # But OOM risk.
        # Let's set them to None for now to ensure stability.
        uris['false_color'] = None
        uris['true_color'] = None
        
        # E. Save DB
        save_observation(tenant_id, aoi_id, year, week, stats, baseline, stats['anomaly_mean'], db, is_fallback=is_fallback)
        save_derived_assets(tenant_id, aoi_id, year, week, 
                            uris['ndvi'], uris['anomaly'], uris['ndvi'], # Quicklook = NDVI
                            uris.get('ndwi'), uris.get('ndmi'), uris.get('savi'), 
                            uris['false_color'], uris['true_color'],
                            stats, db)
        
        update_job_status(job_id, "DONE", db, metrics=stats)


def save_observation(tenant_id: str, aoi_id: str, year: int, week: int, stats: dict, baseline: float, anomaly: float, db: Session, is_fallback: bool = False):
    """Save observation to database"""
    from sqlalchemy import text
    sql = text("""
        INSERT INTO observations_weekly 
        (tenant_id, aoi_id, year, week, pipeline_version, status, valid_pixel_ratio, 
         ndvi_mean, ndvi_p10, ndvi_p50, ndvi_p90, ndvi_std, baseline, anomaly, is_fallback)
        VALUES 
        (:tenant_id, :aoi_id, :year, :week, :pipeline_version, 'OK', :valid_pixel_ratio,
         :ndvi_mean, :ndvi_p10, :ndvi_p50, :ndvi_p90, :ndvi_std, :baseline, :anomaly, :is_fallback)
        ON CONFLICT (tenant_id, aoi_id, year, week, pipeline_version) DO UPDATE
        SET status = 'OK', valid_pixel_ratio = :valid_pixel_ratio, ndvi_mean = :ndvi_mean, is_fallback = :is_fallback
    """)
    db.execute(sql, {
        "tenant_id": tenant_id, "aoi_id": aoi_id, "year": year, "week": week,
        "pipeline_version": settings.pipeline_version, "valid_pixel_ratio": stats['valid_pixel_ratio'],
        "ndvi_mean": stats['ndvi_mean'], "ndvi_p10": stats['ndvi_p10'], "ndvi_p50": stats['ndvi_p50'],
        "ndvi_p90": stats['ndvi_p90'], "ndvi_std": stats['ndvi_std'], "baseline": baseline, "anomaly": anomaly,
        "is_fallback": is_fallback
    })
    db.commit()


def save_observation_no_data(tenant_id: str, aoi_id: str, year: int, week: int, db: Session):
    """Save NO_DATA observation"""
    from sqlalchemy import text
    sql = text("""
        INSERT INTO observations_weekly 
        (tenant_id, aoi_id, year, week, pipeline_version, status, valid_pixel_ratio, is_fallback)
        VALUES 
        (:tenant_id, :aoi_id, :year, :week, :pipeline_version, 'NO_DATA', 0.0, FALSE)
        ON CONFLICT (tenant_id, aoi_id, year, week, pipeline_version) DO UPDATE
        SET status = 'NO_DATA', is_fallback = FALSE
    """)
    db.execute(sql, {
        "tenant_id": tenant_id, "aoi_id": aoi_id, "year": year, "week": week,
        "pipeline_version": settings.pipeline_version
    })
    db.commit()


def update_job_status(job_id: str, status: str, db: Session, metrics: dict = None, error: str = None):
    """Update job status"""
    from sqlalchemy import text
    import json
    
    sql = text("""
        UPDATE jobs 
        SET status = :status, updated_at = now()
        WHERE id = :job_id
    """)
    
    db.execute(sql, {"job_id": job_id, "status": status})
    db.commit()
    
    logger.info("job_status_updated", job_id=job_id, status=status)
