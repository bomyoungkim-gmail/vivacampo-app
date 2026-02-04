import structlog
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
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
                       ndre_uri: str, reci_uri: str, gndvi_uri: str, evi_uri: str,
                       msi_uri: str, nbr_uri: str, bsi_uri: str, ari_uri: str, cri_uri: str,
                       stats: dict,
                       db: Session):
    """Save derived assets to database"""
    from sqlalchemy import text
    
    sql = text("""
        INSERT INTO derived_assets 
        (tenant_id, aoi_id, year, week, pipeline_version, 
         ndvi_s3_uri, anomaly_s3_uri, quicklook_s3_uri,
         ndwi_s3_uri, ndmi_s3_uri, savi_s3_uri, false_color_s3_uri, true_color_s3_uri,
         
         ndre_s3_uri, reci_s3_uri, gndvi_s3_uri, evi_s3_uri,
         msi_s3_uri, nbr_s3_uri, bsi_s3_uri, ari_s3_uri, cri_s3_uri,

         ndvi_mean, ndvi_min, ndvi_max, ndvi_std,
         ndwi_mean, ndwi_min, ndwi_max, ndwi_std,
         ndmi_mean, ndmi_min, ndmi_max, ndmi_std,
         savi_mean, savi_min, savi_max, savi_std,
         anomaly_mean, anomaly_std,
         
         ndre_mean, ndre_std, reci_mean, reci_std,
         gndvi_mean, gndvi_std, evi_mean, evi_std,
         msi_mean, msi_std, nbr_mean, nbr_std,
         bsi_mean, bsi_std, ari_mean, ari_std,
         cri_mean, cri_std)
        VALUES 
        (:tenant_id, :aoi_id, :year, :week, :pipeline_version, 
         :ndvi_uri, :anomaly_uri, :quicklook_uri,
         :ndwi_uri, :ndmi_uri, :savi_uri, :false_color_uri, :true_color_uri,
         :ndre_uri, :reci_uri, :gndvi_uri, :evi_uri,
         :msi_uri, :nbr_uri, :bsi_uri, :ari_uri, :cri_uri,

         :ndvi_mean, :ndvi_min, :ndvi_max, :ndvi_std,
         :ndwi_mean, :ndwi_min, :ndwi_max, :ndwi_std,
         :ndmi_mean, :ndmi_min, :ndmi_max, :ndmi_std,
         :savi_mean, :savi_min, :savi_max, :savi_std,
         :anomaly_mean, :anomaly_std,
         
         :ndre_mean, :ndre_std, :reci_mean, :reci_std,
         :gndvi_mean, :gndvi_std, :evi_mean, :evi_std,
         :msi_mean, :msi_std, :nbr_mean, :nbr_std,
         :bsi_mean, :bsi_std, :ari_mean, :ari_std,
         :cri_mean, :cri_std)
        ON CONFLICT (tenant_id, aoi_id, year, week, pipeline_version) DO UPDATE
        SET ndvi_s3_uri = :ndvi_uri, 
            anomaly_s3_uri = :anomaly_uri, 
            quicklook_s3_uri = :quicklook_uri,
            ndwi_s3_uri = :ndwi_uri,
            ndmi_s3_uri = :ndmi_uri,
            savi_s3_uri = :savi_uri,
            false_color_s3_uri = :false_color_uri,
            true_color_s3_uri = :true_color_uri,
            
            ndre_s3_uri = :ndre_uri, reci_s3_uri = :reci_uri,
            gndvi_s3_uri = :gndvi_uri, evi_s3_uri = :evi_uri,
            msi_s3_uri = :msi_uri, nbr_s3_uri = :nbr_uri,
            bsi_s3_uri = :bsi_uri, ari_s3_uri = :ari_uri,
            cri_s3_uri = :cri_uri,

            ndvi_mean = :ndvi_mean, ndvi_min = :ndvi_min, ndvi_max = :ndvi_max, ndvi_std = :ndvi_std,
            ndwi_mean = :ndwi_mean, ndwi_min = :ndwi_min, ndwi_max = :ndwi_max, ndwi_std = :ndwi_std,
            ndmi_mean = :ndmi_mean, ndmi_min = :ndmi_min, ndmi_max = :ndmi_max, ndmi_std = :ndmi_std,
            savi_mean = :savi_mean, savi_min = :savi_min, savi_max = :savi_max, savi_std = :savi_std,
            anomaly_mean = :anomaly_mean, anomaly_std = :anomaly_std,
            
            ndre_mean = :ndre_mean, ndre_std = :ndre_std,
            reci_mean = :reci_mean, reci_std = :reci_std,
            gndvi_mean = :gndvi_mean, gndvi_std = :gndvi_std,
            evi_mean = :evi_mean, evi_std = :evi_std,
            msi_mean = :msi_mean, msi_std = :msi_std,
            nbr_mean = :nbr_mean, nbr_std = :nbr_std,
            bsi_mean = :bsi_mean, bsi_std = :bsi_std,
            ari_mean = :ari_mean, ari_std = :ari_std,
            cri_mean = :cri_mean, cri_std = :cri_std
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
        "true_color_uri": true_color_uri,
        "ndre_uri": ndre_uri, "reci_uri": reci_uri, "gndvi_uri": gndvi_uri, "evi_uri": evi_uri,
        "msi_uri": msi_uri, "nbr_uri": nbr_uri, "bsi_uri": bsi_uri, "ari_uri": ari_uri, "cri_uri": cri_uri
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
    """
    PROCESS_WEEK job handler.

    With ADR-0007 (Dynamic Tiling), this handler has two modes:
    1. use_dynamic_tiling=True (default): Delegates to CALCULATE_STATS job
       - No COGs generated per-AOI
       - Stats calculated via TiTiler from MosaicJSON
       - 99.9% storage reduction

    2. use_dynamic_tiling=False (legacy): Full COG pipeline
       - Downloads bands, calculates indices, uploads COGs to S3
       - Used for rollback or specific use cases
    """
    import asyncio

    logger.info("process_week_start", job_id=job_id, use_dynamic_tiling=settings.use_dynamic_tiling)
    update_job_status(job_id, "RUNNING", db)

    # ADR-0007: Dynamic Tiling Mode
    if settings.use_dynamic_tiling:
        try:
            # Delegate to CALCULATE_STATS which uses TiTiler + MosaicJSON
            from worker.jobs.calculate_stats import calculate_stats_handler

            logger.info(
                "process_week_dynamic_tiling_mode",
                job_id=job_id,
                message="Delegating to CALCULATE_STATS (no COG generation)"
            )

            # Call calculate_stats directly
            result = calculate_stats_handler(job_id, payload, db)

            logger.info("process_week_dynamic_tiling_complete", job_id=job_id, result=result)
            return result

        except Exception as e:
            logger.error("process_week_dynamic_tiling_failed", job_id=job_id, error=str(e), exc_info=True)
            update_job_status(job_id, "FAILED", db, error=str(e))
            raise

    # Legacy Mode: Full COG pipeline
    logger.info("process_week_legacy_mode", job_id=job_id, message="Using legacy COG pipeline")
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
    
    # 1. Search (Optical + Radar)
    start_date, end_date = get_week_date_range(year, week)
    aoi_geom = get_aoi_geometry(aoi_id, db)
    client = get_stac_client()
    
    # --- WEATHER FETCHING (Independent) ---
    try:
        if start_date.date() > date.today():
            logger.info("weather_fetch_skipped_future_window", start_date=str(start_date), end_date=str(end_date))
        else:
            bounds = rasterio.features.bounds(aoi_geom)
            centroid_lon = (bounds[0] + bounds[2]) / 2
            centroid_lat = (bounds[1] + bounds[3]) / 2

            clamped_end = min(end_date.date(), date.today())
            weather_data = await client.fetch_weather_history(
                centroid_lat, centroid_lon,
                start_date.strftime("%Y-%m-%d"),
                clamped_end.strftime("%Y-%m-%d")
            )

            if weather_data:
                save_weather_data(tenant_id, aoi_id, weather_data, db)
                logger.info("weather_data_saved", days=len(weather_data))
    except Exception as e:
        logger.error("weather_fetch_failed", exc_info=e)
        # Non-blocking, continue


    # --- OPTICAL SEARCH ---
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
    
    # --- RADAR SEARCH (Sentinel-1) ---
    # Radar is weather independent, so we can likely find scenes even if optical fails logic
    # But for now, let's keep it simple: if optical fails completely (even fallback), we still try radar?
    # Yes.
    
    radar_scenes = await client.search_scenes(
        aoi_geom, start_date, end_date, max_cloud_cover=100, collections=["sentinel-1-rtc"]
    )
    # Filter for VV and VH availability
    valid_radar = [s for s in radar_scenes if 'vv' in s['assets'] and 'vh' in s['assets']]
    best_radar = valid_radar[0] if valid_radar else None
    
    
    if not valid_scenes and not best_radar:
         save_observation_no_data(tenant_id, aoi_id, year, week, db)
         update_job_status(job_id, "DONE", db)
         return
    
    # ---------------------------------------------------------
    # Processing Loop
    # ---------------------------------------------------------
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # D. Upload to S3
        s3 = S3Client()
        prefix = f"tenant={tenant_id}/aoi={aoi_id}/year={year}/week={week}/pipeline={settings.pipeline_version}/"
        uris = {}
        
        # --- RADAR PROCESSING ---
        radar_stats = {}
        if best_radar:
            try:
                vv_path = os.path.join(tmpdir, "vv.tif")
                vh_path = os.path.join(tmpdir, "vh.tif")
                
                # Fetch VV/VH
                await asyncio.gather(
                    client.download_and_clip_band(best_radar['assets']['vv'], aoi_geom, vv_path),
                    client.download_and_clip_band(best_radar['assets']['vh'], aoi_geom, vh_path)
                )
                
                with rasterio.open(vv_path) as src:
                    vv = src.read(1)
                    radar_profile = src.profile
                with rasterio.open(vh_path) as src:
                    vh = src.read(1)
                
                # Calculate RVI
                rvi = await client.calculate_rvi(vv, vh)
                rvi_path = os.path.join(tmpdir, "rvi.tif")
                export_cog(rvi, rvi_path, radar_profile)
                
                # Calculate Ratio
                ratio = await client.calculate_radar_ratio(vv, vh)
                ratio_path = os.path.join(tmpdir, "radar_ratio.tif")
                export_cog(ratio, ratio_path, radar_profile)
                
                # Calc Stats
                radar_stats.update(calculate_band_stats(rvi, "rvi"))
                radar_stats.update(calculate_band_stats(ratio, "ratio"))
                
                # Upload
                uris['rvi'] = s3.upload_file(rvi_path, prefix + "rvi.tif")
                uris['ratio'] = s3.upload_file(ratio_path, prefix + "radar_ratio.tif")
                uris['vv'] = s3.upload_file(vv_path, prefix + "vv.tif")
                uris['vh'] = s3.upload_file(vh_path, prefix + "vh.tif")
                
                # Save to DB
                save_radar_assets(tenant_id, aoi_id, year, week, uris, radar_stats, db)
                
                del vv, vh, rvi, ratio
                gc.collect()
                
            except Exception as e:
                logger.error("radar_processing_failed", exc_info=e)
                # Continue to optical

        # --- OPTICAL PROCESSING ---
        if not valid_scenes:
            # If no optical but we had radar, we mark job as done (status OK but no optical data)
            # Actually save_observation expects ndvi stats.
            # We should probably save NO_DATA for optical part if missing.
            save_observation_no_data(tenant_id, aoi_id, year, week, db)
            update_job_status(job_id, "DONE", db)
            return

        # Use best optical scene
        best_scene = sorted(valid_scenes, key=lambda s: s['cloud_cover'])[0]
        logger.info("selected_best_scene", scene_id=best_scene['id'], is_fallback=is_fallback)
        
        band_paths = {}
        profile = None
        
        # Parallel Download Optical
        logger.info("DEBUG_TRACE: Starting parallel download (Semaphore=2)", job_id=job_id)
        # Added 'rededge' (B05) and 'swir2' (B12) for advanced indices
        required_bands = ['red', 'green', 'blue', 'nir', 'swir', 'swir2', 'rededge', 'scl']
        sem = asyncio.Semaphore(2)

        async def fetch_band(b):
            async with sem:
                href = best_scene['assets'].get(b)
                if not href: 
                    return None
                p = os.path.join(tmpdir, f"{b}.tif")
                try:
                    await asyncio.wait_for(
                        client.download_and_clip_band(href, aoi_geom, p),
                        timeout=300.0
                    )
                    return (b, p)
                except Exception as e:
                    logger.error("band_download_failed", band=b, error=str(e))
                    return None

        results = await asyncio.gather(*[fetch_band(b) for b in required_bands])
        
        for res in results:
            if res:
                b, p = res
                band_paths[b] = p
                try:
                    if b == 'red' and profile is None:
                         with rasterio.open(p) as src: profile = src.profile
                except: pass

        if 'red' not in band_paths or 'nir' not in band_paths:
            logger.error("missing_critical_bands")
            save_observation_no_data(tenant_id, aoi_id, year, week, db)
            update_job_status(job_id, "DONE", db)
            return

        gc.collect()

        # Mask Clouds
        if 'scl' in band_paths:
            scl = rasterio.open(band_paths['scl']).read(1)
            bad_mask = np.isin(scl, [0, 1, 3, 8, 9, 10])
            del scl
            
            for b in band_paths:
                if b == 'scl': continue
                with rasterio.open(band_paths[b]) as src:
                    data = src.read(1)
                    # Resize mask if needed
                    if data.shape != bad_mask.shape:
                        h, w = data.shape
                        hm, wm = bad_mask.shape
                        y = (np.arange(h) * (hm / h)).astype(int)
                        x = (np.arange(w) * (wm / w)).astype(int)
                        current_mask = bad_mask[np.clip(y, 0, hm-1)[:, None], np.clip(x, 0, wm-1)]
                    else:
                        current_mask = bad_mask
                    
                    data = np.where(current_mask, np.nan, data).astype('float32')
                    
                    with rasterio.open(band_paths[b], 'w', **profile) as dst:
                        dst.write(data, 1)
                    del data
                    gc.collect()
            del bad_mask
            gc.collect()

        # Calculate Indices
        out_paths = {}
        def load_band(name): return rasterio.open(band_paths[name]).read(1)
        def save_idx(name, arr):
             p = os.path.join(tmpdir, f"{name}.tif")
             export_cog(arr, p, profile)
             out_paths[name] = p
             return arr 

        # NDVI
        red = load_band('red')
        nir = load_band('nir')
        ndvi = await client.calculate_ndvi(red, nir)
        save_idx('ndvi', ndvi)
        
        valid_pixels = ndvi[~np.isnan(ndvi)]
        valid_pixel_ratio = len(valid_pixels) / ndvi.size if ndvi.size > 0 else 0
        
        if valid_pixel_ratio < settings.min_valid_pixel_ratio:
              save_observation_no_data(tenant_id, aoi_id, year, week, db)
              update_job_status(job_id, "DONE", db)
              return

        stats = {}
        stats.update(calculate_band_stats(ndvi, "ndvi"))
        
        savi = await client.calculate_savi(red, nir)
        save_idx('savi', savi)
        stats.update(calculate_band_stats(savi, "savi"))
        del savi
        
        del red
        if 'green' in band_paths:
            green = load_band('green')
            ndwi = await client.calculate_ndwi(green, nir)
            save_idx('ndwi', ndwi)
            stats.update(calculate_band_stats(ndwi, "ndwi"))
            del ndwi, green
            
        if 'swir' in band_paths:
            swir = load_band('swir')
            ndmi = await client.calculate_ndmi(nir, swir)
            save_idx('ndmi', ndmi)
            stats.update(calculate_band_stats(ndmi, "ndmi"))
            del ndmi, swir
        
        del nir
        gc.collect()

        # Anomaly
        baseline = 0.60
        anomaly_map = ndvi - baseline
        save_idx('anomaly', anomaly_map)
        stats.update(calculate_band_stats(anomaly_map, "anomaly"))

        # --- ADVANCED INDICES CALCULATIONS ---
        
        # Load extra bands if available
        blue = load_band('blue') if 'blue' in band_paths else None
        rededge = load_band('rededge') if 'rededge' in band_paths else None
        swir2 = load_band('swir2') if 'swir2' in band_paths else None
        green = load_band('green') if 'green' in band_paths else None
        # swir (B11) already loaded as swir/ndmi context? Re-load to be safe or reuse
        swir = load_band('swir') if 'swir' in band_paths else None
        # red, nir already loaded
        red = load_band('red')
        nir = load_band('nir')

        # 1. NDRE (Normalized Difference Red Edge) = (NIR - RedEdge) / (NIR + RedEdge)
        if rededge is not None:
            ndre = (nir - rededge) / (nir + rededge + 1e-6)
            save_idx('ndre', ndre)
            stats.update(calculate_band_stats(ndre, "ndre"))
            
            # 2. RECI (Red-Edge Chlorophyll Index) = (NIR / RedEdge) - 1
            reci = (nir / (rededge + 1e-6)) - 1
            save_idx('reci', reci)
            stats.update(calculate_band_stats(reci, "reci"))
            
            # 3. ARI (Anthocyanin Reflectance Index) = (1/Green) - (1/RedEdge)
            if green is not None:
                ari = (1 / (green + 1e-6)) - (1 / (rededge + 1e-6))
                save_idx('ari', ari)
                stats.update(calculate_band_stats(ari, "ari"))
        else:
            logger.warn("missing_band_rededge_skipping_indices")

        # 4. GNDVI (Green NDVI) = (NIR - Green) / (NIR + Green)
        if green is not None:
            gndvi = (nir - green) / (nir + green + 1e-6)
            save_idx('gndvi', gndvi)
            stats.update(calculate_band_stats(gndvi, "gndvi"))

        # 5. EVI (Enhanced Vegetation Index) = 2.5 * ((NIR - Red) / (NIR + 6 * Red - 7.5 * Blue + 1))
        if blue is not None:
            evi = 2.5 * ((nir - red) / (nir + 6 * red - 7.5 * blue + 1 + 1e-6))
            save_idx('evi', evi)
            stats.update(calculate_band_stats(evi, "evi"))
            
            # 8. BSI (Bare Soil Index) = ((SWIR + Red) - (NIR + Blue)) / ((SWIR + Red) + (NIR + Blue))
            if swir is not None:
                 bsi = ((swir + red) - (nir + blue)) / ((swir + red) + (nir + blue) + 1e-6)
                 save_idx('bsi', bsi)
                 stats.update(calculate_band_stats(bsi, "bsi"))

            # 9. CRI (Carotenoid) - Plan: (1/B2) - (1/B5) * B8? Let's use simplified CRI1 = (1/Blue) - (1/Green) standard
            # Actually respecting the plan's specific request for CRI logic if possible or standard.
            # Let's use CRI1 = (1/Blue) - (1/Green) as it is robust.
            if green is not None:
                cri = (1 / (blue + 1e-6)) - (1 / (green + 1e-6))
                save_idx('cri', cri)
                stats.update(calculate_band_stats(cri, "cri"))

        # 6. MSI (Moisture Stress Index) = SWIR / NIR
        if swir is not None:
            msi = swir / (nir + 1e-6)
            save_idx('msi', msi)
            stats.update(calculate_band_stats(msi, "msi"))

        # 7. NBR (Normalized Burn Ratio) = (NIR - SWIR2) / (NIR + SWIR2)
        if swir2 is not None:
            nbr = (nir - swir2) / (nir + swir2 + 1e-6)
            save_idx('nbr', nbr)
            stats.update(calculate_band_stats(nbr, "nbr"))

        del blue, rededge, swir, swir2, green
        
        if valid_pixels.size > 0:
            stats['ndvi_p10'] = float(np.nanpercentile(valid_pixels, 10))
            stats['ndvi_p50'] = float(np.nanpercentile(valid_pixels, 50))
            stats['ndvi_p90'] = float(np.nanpercentile(valid_pixels, 90))
        else:
            stats['ndvi_p10'] = 0.0; stats['ndvi_p50'] = 0.0; stats['ndvi_p90'] = 0.0
            
        stats['valid_pixel_ratio'] = valid_pixel_ratio
        del ndvi, valid_pixels, anomaly_map
        gc.collect()
        
        # Upload Optical to S3
        for k, p in out_paths.items():
            uris[k] = s3.upload_file(p, prefix + f"{k}.tif")

        uris['false_color'] = None
        uris['true_color'] = None
        
        # E. Save DB
        save_observation(tenant_id, aoi_id, year, week, stats, baseline, stats['anomaly_mean'], db, is_fallback=is_fallback)
        save_derived_assets(tenant_id, aoi_id, year, week, 
                            uris['ndvi'], uris.get('anomaly'), uris.get('ndvi'), # Quicklook as NDVI
                            uris.get('ndwi'), uris.get('ndmi'), uris.get('savi'), 
                            uris.get('false_color'), uris.get('true_color'),
                            uris.get('ndre'), uris.get('reci'), uris.get('gndvi'), uris.get('evi'),
                            uris.get('msi'), uris.get('nbr'), uris.get('bsi'),
                            uris.get('ari'), uris.get('cri'),
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
        SET status = :status, error_message = :error_message, updated_at = now()
        WHERE id = :job_id
    """)
    
    db.execute(sql, {"job_id": job_id, "status": status, "error_message": error})
    db.commit()
    
    logger.info("job_status_updated", job_id=job_id, status=status)

def save_radar_assets(tenant_id, aoi_id, year, week, uris, stats, db):
    from sqlalchemy import text
    sql = text("""
        INSERT INTO derived_radar_assets 
        (tenant_id, aoi_id, year, week, pipeline_version, 
         rvi_s3_uri, ratio_s3_uri, vv_s3_uri, vh_s3_uri,
         rvi_mean, rvi_std, ratio_mean, ratio_std)
        VALUES 
        (:tenant_id, :aoi_id, :year, :week, :pipeline_version,
         :rvi_s3_uri, :ratio_s3_uri, :vv_s3_uri, :vh_s3_uri,
         :rvi_mean, :rvi_std, :ratio_mean, :ratio_std)
        ON CONFLICT (tenant_id, aoi_id, year, week, pipeline_version) DO UPDATE
        SET rvi_s3_uri = :rvi_s3_uri, ratio_s3_uri = :ratio_s3_uri, 
            vv_s3_uri = :vv_s3_uri, vh_s3_uri = :vh_s3_uri,
            rvi_mean = :rvi_mean, ratio_mean = :ratio_mean
    """)
    
    db.execute(sql, {
        "tenant_id": tenant_id, "aoi_id": aoi_id, "year": year, "week": week,
        "pipeline_version": settings.pipeline_version,
        "rvi_s3_uri": uris.get('rvi'), "ratio_s3_uri": uris.get('ratio'),
        "vv_s3_uri": uris.get('vv'), "vh_s3_uri": uris.get('vh'),
        "rvi_mean": stats.get('rvi_mean'), "rvi_std": stats.get('rvi_std'),
        "ratio_mean": stats.get('ratio_mean'), "ratio_std": stats.get('ratio_std')
    })
    db.commit()

def save_weather_data(tenant_id, aoi_id, data_list, db):
    from sqlalchemy import text
    sql = text("""
        INSERT INTO derived_weather_daily
        (tenant_id, aoi_id, date, temp_max, temp_min, precip_sum, et0_fao)
        VALUES
        (:tenant_id, :aoi_id, :date, :temp_max, :temp_min, :precip_sum, :et0_fao)
        ON CONFLICT (tenant_id, aoi_id, date) DO UPDATE
        SET temp_max = :temp_max, temp_min = :temp_min, precip_sum = :precip_sum, et0_fao = :et0_fao
    """)
    
    for row in data_list:
        db.execute(sql, {
            "tenant_id": tenant_id, "aoi_id": aoi_id,
            "date": row['date'],
            "temp_max": row['temp_max'], "temp_min": row['temp_min'],
            "precip_sum": row['precip_sum'], "et0_fao": row['et0_fao']
        })
    db.commit()
