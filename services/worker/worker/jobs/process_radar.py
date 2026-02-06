import structlog
from sqlalchemy.orm import Session
from worker.config import settings
from worker.shared.aws_clients import S3Client
import tempfile
import os
import rasterio
import numpy as np

logger = structlog.get_logger()

def export_cog(data: np.ndarray, output_path: str, profile: dict):
    """Export data as Cloud Optimized GeoTIFF"""
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

def ensure_radar_table_exists(db: Session):
    """Ensure derived_radar_assets table exists"""
    from sqlalchemy import text
    sql = text("""
        CREATE TABLE IF NOT EXISTS derived_radar_assets (
            tenant_id UUID NOT NULL,
            aoi_id UUID NOT NULL,
            year INTEGER NOT NULL,
            week INTEGER NOT NULL,
            pipeline_version VARCHAR(50) NOT NULL,
            
            rvi_s3_uri TEXT,
            ratio_s3_uri TEXT,
            vh_s3_uri TEXT,
            vv_s3_uri TEXT,
            
            rvi_mean FLOAT,
            rvi_std FLOAT,
            ratio_mean FLOAT,
            ratio_std FLOAT,
            
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            
            PRIMARY KEY (tenant_id, aoi_id, year, week, pipeline_version)
        );
    """)
    db.execute(sql)
    db.commit()

def save_radar_assets(tenant_id: str, aoi_id: str, year: int, week: int, 
                       rvi_uri: str, ratio_uri: str, vh_uri: str, vv_uri: str,
                       stats: dict, db: Session):
    """Save radar assets to database"""
    from sqlalchemy import text
    
    ensure_radar_table_exists(db)
    
    sql = text("""
        INSERT INTO derived_radar_assets 
        (tenant_id, aoi_id, year, week, pipeline_version, 
         rvi_s3_uri, ratio_s3_uri, vh_s3_uri, vv_s3_uri,
         rvi_mean, rvi_std, ratio_mean, ratio_std)
        VALUES 
        (:tenant_id, :aoi_id, :year, :week, :pipeline_version, 
         :rvi_uri, :ratio_uri, :vh_uri, :vv_uri,
         :rvi_mean, :rvi_std, :ratio_mean, :ratio_std)
        ON CONFLICT (tenant_id, aoi_id, year, week, pipeline_version) DO UPDATE
        SET rvi_s3_uri = :rvi_uri, 
            ratio_s3_uri = :ratio_uri, 
            vh_s3_uri = :vh_uri,
            vv_s3_uri = :vv_uri,
            rvi_mean = :rvi_mean, rvi_std = :rvi_std,
            ratio_mean = :ratio_mean, ratio_std = :ratio_std,
            updated_at = NOW()
    """)
    
    params = {
        "tenant_id": tenant_id, "aoi_id": aoi_id, "year": year, "week": week,
        "pipeline_version": settings.pipeline_version,
        "rvi_uri": rvi_uri, "ratio_uri": ratio_uri, "vh_uri": vh_uri, "vv_uri": vv_uri,
        "rvi_mean": stats.get('rvi_mean', 0), "rvi_std": stats.get('rvi_std', 0),
        "ratio_mean": stats.get('ratio_mean', 0), "ratio_std": stats.get('ratio_std', 0)
    }
    
    db.execute(sql, params)
    db.commit()

def update_job_status(job_id: str, status: str, db: Session, error: str = None):
    from sqlalchemy import text
    sql = text("UPDATE jobs SET status = :status, error_message = :error_message, updated_at = now() WHERE id = :job_id")
    db.execute(sql, {"job_id": job_id, "status": status, "error_message": error})
    db.commit()

async def process_radar_week_async(job_id: str, payload: dict, db: Session):
    from worker.pipeline.stac_client import get_stac_client
    from worker.shared.utils import get_week_date_range, get_aoi_geometry
    import gc
    
    tenant_id = payload['tenant_id']
    aoi_id = payload['aoi_id']
    year = payload['year']
    year = payload['year']
    week = payload['week']
    
    # Ensure table exists regardless of data finding (prevents Frontend 500s)
    ensure_radar_table_exists(db)
    
    # 1. Search Scenes
    start_date, end_date = get_week_date_range(year, week)
    aoi_geom = get_aoi_geometry(aoi_id, db)
    client = get_stac_client()
    
    # Search Sentinel-1 RTC
    scenes = await client.search_scenes(
        aoi_geom, start_date, end_date, 
        max_cloud_cover=100, # Not used for S1 but API requires arg
        collections=["sentinel-1-rtc"] # Planetary Computer collection
    )
    
    # Filter for valid VV/VH
    valid_scenes = [s for s in scenes if s['assets'].get('vv') and s['assets'].get('vh')]
    
    if not valid_scenes:
         # No S1 data for this week (uncommon but possible)
         update_job_status(job_id, "DONE", db)
         return
    
    # Pick first available scene
    best_scene = valid_scenes[0]
    logger.info("selected_best_radar_scene", scene_id=best_scene['id'])
    
    # 3. Download and Process
    with tempfile.TemporaryDirectory() as tmpdir:
        band_paths = {}
        profile = None
        
        # Download VV and VH
        for band in ['vv', 'vh']:
            href = best_scene['assets'].get(band)
            p = os.path.join(tmpdir, f"{band}.tif")
            await client.download_and_clip_band(href, aoi_geom, p)
            band_paths[band] = p
            
            if band == 'vv' and profile is None:
                with rasterio.open(p) as src: profile = src.profile
        
        # Load Data
        with rasterio.open(band_paths['vv']) as src: vv = src.read(1)
        with rasterio.open(band_paths['vh']) as src: vh = src.read(1)
        
        # 4. Calculate Indices
        # 4. Calculate Indices
        # Ensure Linear Scale for RVI
        # RTC on Planetary Computer is typically float32 linear power.
        # But if we accidentally get dB (usually negative values for vegetation), we must convert.
        if np.nanmean(vv) < 0:
            logger.info("detect_db_scale_converting_to_linear")
            vv = 10 ** (vv / 10.0)
            vh = 10 ** (vh / 10.0)

        # Calculate RVI (Radar Vegetation Index)
        # Formula: 4*VH / (VV + VH)
        # Range: 0 (bare soil) to 1 (dense vegetation)
        numerator = 4 * vh
        denominator = vv + vh
        denominator = np.where(denominator == 0, 0.0001, denominator) # Avoid div/0
        rvi = numerator / denominator
        rvi = np.clip(rvi, 0, 1) # Ensure valid range

        # Calculate VH/VV Ratio (Volume Scattering vs Surface Scattering)
        vv_safe = np.where(vv == 0, 0.0001, vv)
        ratio = vh / vv_safe
        
        # Stats
        stats = {}
        def calc_stats(arr, name):
            v = arr[~np.isnan(arr)]
            if v.size == 0: return {f"{name}_mean": 0, f"{name}_std": 0}
            return {f"{name}_mean": float(np.mean(v)), f"{name}_std": float(np.std(v))}
            
        stats.update(calc_stats(rvi, "rvi"))
        stats.update(calc_stats(ratio, "ratio"))
        
        # 6. Export and Upload
        s3 = S3Client()
        prefix = f"tenant={tenant_id}/aoi={aoi_id}/year={year}/week={week}/radar/"
        
        def up(name, data):
             p = os.path.join(tmpdir, f"{name}.tif")
             export_cog(data, p, profile)
             return s3.upload_file(p, prefix + f"{name}.tif")
        
        rvi_uri = up("rvi", rvi)
        ratio_uri = up("ratio", ratio)
        vh_uri = up("vh", vh)
        vv_uri = up("vv", vv)
        
        # 7. Save DB
        save_radar_assets(tenant_id, aoi_id, year, week, 
                          rvi_uri, ratio_uri, vh_uri, vv_uri,
                          stats, db)
        
        update_job_status(job_id, "DONE", db)

def process_radar_week_handler(job_id: str, payload: dict, db: Session):
    """PROCESS_RADAR_WEEK job handler Wrapper"""
    import asyncio
    logger.info("process_radar_week_start", job_id=job_id)
    update_job_status(job_id, "RUNNING", db)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(process_radar_week_async(job_id, payload, db))
        finally:
            loop.close()
    except Exception as e:
        logger.error("process_radar_week_failed", job_id=job_id, exc_info=e)
        update_job_status(job_id, "FAILED", db, error=str(e))
