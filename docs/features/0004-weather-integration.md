# FEAT-0004 — Weather Integration

Date: 2026-01-10
Owner: Backend Team
Status: Done

## Goal
Provide localized weather data per AOI to correlate vegetation indices with meteorological conditions.

**User value:** Users can understand why crop health changed (e.g., drought stress after low rainfall) and plan irrigation accordingly.

## Scope
**In scope:**
- Daily weather data per AOI (temperature, precipitation, humidity)
- Evapotranspiration calculation (ET0 - reference)
- Historical weather (30 days)
- Weather forecast (7 days)
- Integration with Open-Meteo API (free, no API key required)

**Out of scope:**
- Hyperlocal weather stations integration
- Weather alerts/notifications
- Irrigation scheduling recommendations

## User Stories
- **As a farmer**, I want to see rainfall data for my fields, so that I can understand water availability.
- **As an agronomist**, I want to correlate NDVI drops with weather patterns, so that I can diagnose stress causes.
- **As a farm manager**, I want to see ET0 values, so that I can estimate crop water requirements.

## UX Notes
**Weather Card:**
- Current conditions (temp, humidity, wind)
- 7-day forecast mini-chart
- Precipitation totals (last 7/14/30 days)
- ET0 accumulated

**Charts:**
- Temperature (min/max) line chart
- Precipitation bar chart
- Combined NDVI + Rainfall overlay

## Contract Changes
**API:**
- Endpoint: `GET /v1/aois/{aoi_id}/weather`
- Query params: `start_date`, `end_date`
- Response:
  ```json
  {
    "weather": [
      {
        "date": "2026-01-20",
        "temp_min": 18.5,
        "temp_max": 32.1,
        "temp_avg": 25.3,
        "precipitation_mm": 12.5,
        "humidity_avg": 68,
        "et0_mm": 5.2
      }
    ],
    "summary": {
      "total_precipitation_mm": 85.2,
      "total_et0_mm": 42.1,
      "avg_temp": 26.8
    }
  }
  ```

**Domain:**
- Entity: `DerivedWeatherDaily`
- Service: `fetch_weather_for_aoi(aoi_id, centroid, date_range)`
- Integration: Open-Meteo API client

**Data:**
- Table: `derived_weather_daily`
- Columns: `id`, `aoi_id`, `date`, `temp_min`, `temp_max`, `temp_avg`, `precipitation_mm`, `humidity_avg`, `wind_speed_avg`, `et0_mm`
- Index: `(aoi_id, date)` unique

## Acceptance Criteria
- [x] System fetches weather data from Open-Meteo for AOI centroid
- [x] System stores daily weather records per AOI
- [x] System calculates ET0 using FAO Penman-Monteith
- [x] User sees weather chart in AOI details
- [x] Weather tab shows 30-day history and 7-day forecast
- [x] System handles API failures gracefully (cached data fallback)

## Observability
**Logs:**
- `weather.fetched` (aoi_id, date_range, source=open_meteo)
- `weather.fetch_failed` (aoi_id, error, fallback_used)

**Metrics:**
- `weather_api_requests_total` (counter)
- `weather_api_latency_seconds` (histogram)
- `weather_cache_hits_total` (counter)

## Testing
**Unit tests:**
- ET0 calculation formula
- Date range handling

**Integration tests:**
- Open-Meteo API integration (stubbed in tests)
- Weather data retrieval and storage

## Status
Done - Deployed 2026-01-15
