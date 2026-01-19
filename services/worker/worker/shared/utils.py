from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
import json

def get_week_date_range(year: int, week: int):
    """Get start and end date (datetime) for a given ISO year and week"""
    # specific calculation for start of ISO week
    # This is a simplifed version, robust version uses isocalendar
    first_day_of_year = datetime(year, 1, 4)  # 4th Jan is always in 1st ISO week
    first_monday = first_day_of_year - timedelta(days=first_day_of_year.isoweekday() - 1)
    
    start_date = first_monday + timedelta(weeks=week - 1)
    end_date = start_date + timedelta(days=6)
    
    # Return as objects, or strings? Stac client expects datetime usually?
    # Let's check usage. client.search_scenes takes datetime.
    return start_date, end_date

def get_aoi_geometry(aoi_id: str, db: Session):
    """Get AOI geometry as dict (GeoJSON)"""
    # Fetch geometry from DB. Assuming it's in WKT or GeoJSON column
    # The schema has a 'geometry' column which is PostGIS Geometry(Polygon, 4326)
    # We can cast it to GeoJSON
    
    sql = text("""
        SELECT ST_AsGeoJSON(geom) as geojson
        FROM aois 
        WHERE id = :aoi_id
    """)
    
    result = db.execute(sql, {"aoi_id": aoi_id}).fetchone()
    if not result:
        raise ValueError(f"AOI {aoi_id} not found")
        
    geojson_str = result[0]
    return json.loads(geojson_str)
