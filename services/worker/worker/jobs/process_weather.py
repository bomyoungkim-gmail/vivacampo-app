
import structlog
import requests
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from worker.config import settings
import numpy as np

logger = structlog.get_logger()

# -----------------------------------------------------------------------------
# Database Utils
# -----------------------------------------------------------------------------

def ensure_weather_table_exists(db: Session):
    """Ensure derived_weather_daily table exists"""
    sql = text("""
        CREATE TABLE IF NOT EXISTS derived_weather_daily (
            tenant_id UUID NOT NULL,
            aoi_id UUID NOT NULL,
            date DATE NOT NULL,
            
            temp_max FLOAT,
            temp_min FLOAT,
            precip_sum FLOAT,
            et0_fao FLOAT,
            
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            
            PRIMARY KEY (tenant_id, aoi_id, date)
        );
        CREATE INDEX IF NOT EXISTS idx_weather_aoi_date ON derived_weather_daily (aoi_id, date);
    """)
    db.execute(sql)
    db.commit()

def save_weather_batch(tenant_id: str, aoi_id: str, data: list, db: Session):
    """Batch upsert weather data"""
    if not data:
        return

    ensure_weather_table_exists(db)
    
    # Construct massive upsert using execute many (fastest with drivers usually) or manual loop
    # We will use simple loop with upsert for safety and simplicity in this context
    
    sql = text("""
        INSERT INTO derived_weather_daily 
        (tenant_id, aoi_id, date, temp_max, temp_min, precip_sum, et0_fao)
        VALUES 
        (:tenant_id, :aoi_id, :date, :temp_max, :temp_min, :precip_sum, :et0_fao)
        ON CONFLICT (tenant_id, aoi_id, date) DO UPDATE
        SET temp_max = EXCLUDED.temp_max,
            temp_min = EXCLUDED.temp_min,
            precip_sum = EXCLUDED.precip_sum,
            et0_fao = EXCLUDED.et0_fao,
            updated_at = NOW();
    """)
    
    # Prepare list of dicts
    params_list = []
    for d in data:
        params_list.append({
            "tenant_id": tenant_id,
            "aoi_id": aoi_id,
            "date": d['date'],
            "temp_max": d['temp_max'],
            "temp_min": d['temp_min'],
            "precip_sum": d['precip_sum'],
            "et0_fao": d['et0_fao']
        })
        
    db.execute(sql, params_list)
    db.commit()

# -----------------------------------------------------------------------------
# Business Logic
# -----------------------------------------------------------------------------

async def fetch_open_meteo_history(lat: float, lon: float, start_date: str, end_date: str):
    """Fetch Open-Meteo Archive"""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration",
        "timezone": "auto"
    }
    
    logger.info("fetching_open_meteo", params=params)
    
    # Run in thread executor to avoid blocking async loop with requests
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: requests.get(url, params=params))
    response.raise_for_status()
    return response.json()

def update_job_status(job_id: str, status: str, db: Session, error: str = None):
    sql = text("UPDATE jobs SET status = :status, error_message = :err, updated_at = now() WHERE id = :job_id")
    db.execute(sql, {"job_id": job_id, "status": status, "err": error})
    db.commit()

async def process_weather_history_async(job_id: str, payload: dict, db: Session):
    from worker.shared.utils import get_aoi_geometry
    from shapely import wkt
    import shapely.geometry
    
    tenant_id = payload.get('tenant_id')
    aoi_id = payload.get('aoi_id')
    
    # Determine Date Range
    # Default: Past 10 years for full history backfill
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365 * 10) # 10 years
    
    # If payload specifies range, use it
    if payload.get('start_date'):
        start_date = datetime.fromisoformat(payload['start_date']).date()
    if payload.get('end_date'):
        end_date = datetime.fromisoformat(payload['end_date']).date()
        
    start_str = start_date.isoformat()
    end_str = end_date.isoformat()
    
    # Get Centroid
    geom_wkt = get_aoi_geometry(aoi_id, db)
    if not geom_wkt:
        raise ValueError("AOI Geometry not found")
        
    polygon = wkt.loads(geom_wkt)
    centroid = polygon.centroid
    lat, lon = centroid.y, centroid.x
    
    # Fetch Data
    data = await fetch_open_meteo_history(lat, lon, start_str, end_str)
    
    # Transform
    daily = data.get('daily', {})
    dates = daily.get('time', [])
    temp_max = daily.get('temperature_2m_max', [])
    temp_min = daily.get('temperature_2m_min', [])
    precip = daily.get('precipitation_sum', [])
    et0 = daily.get('et0_fao_evapotranspiration', [])
    
    records = []
    for i, date_str in enumerate(dates):
        # Handle potential None values from API
        tmax = temp_max[i] if temp_max[i] is not None else 0
        tmin = temp_min[i] if temp_min[i] is not None else 0
        psum = precip[i] if precip[i] is not None else 0
        e0 = et0[i] if et0[i] is not None else 0
        
        records.append({
            "date": date_str,
            "temp_max": tmax,
            "temp_min": tmin,
            "precip_sum": psum,
            "et0_fao": e0
        })
        
    # Batch Save
    save_weather_batch(tenant_id, aoi_id, records, db)
    
    update_job_status(job_id, "DONE", db)

def process_weather_history_handler(job_id: str, payload: dict, db: Session):
    logger.info("process_weather_history_start", job_id=job_id)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(process_weather_history_async(job_id, payload, db))
        finally:
            loop.close()
    except Exception as e:
        logger.error("process_weather_failed", job_id=job_id, exc_info=e)
        update_job_status(job_id, "FAILED", db, error=str(e))
