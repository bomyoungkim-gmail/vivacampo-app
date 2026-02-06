# ADR-0010 — Correlation API and Analysis Tab

Date: 2026-02-04
Status: Proposed
Owners: Intelligence Team

## Context

Users currently view vegetation indices, radar data, and weather data in **separate tabs**, making it difficult to understand cause-effect relationships:
- "Why did NDVI increase last week?" → Need to check Weather tab for rain
- "Is the vigor drop due to drought or disease?" → Need to correlate NDMI with rain data

**Existing capabilities**:
- ✅ Vegetation indices (NDVI, NDRE, etc.) in Health/Water/Nutrition tabs
- ✅ Radar data (RVI) in Radar tab
- ✅ Weather data (rain, temp) in Weather tab
- ❌ Correlation analysis - Missing
- ❌ Auto-generated insights - Missing

**User pain point**: Requires GIS expertise to manually correlate data across tabs.

## Decision

Create **Correlation API** and **Analysis Tab** to combine data and generate insights.

### 1. Backend: Correlation API

**Endpoint**: `/v1/aois/{aoi_id}/correlation/vigor-climate`

**Response**:
```json
{
  "data": [
    {
      "date": "2026-01-15",
      "ndvi": 0.75,
      "rvi": null,
      "rain_mm": 12.5,
      "temp_avg": 28.3,
      "cloud_cover": 80
    },
    {
      "date": "2026-01-22",
      "ndvi": null,  // Cloudy day
      "rvi": 0.45,   // Radar fallback
      "rain_mm": 0,
      "temp_avg": 30.1
    }
  ],
  "insights": [
    "Chuva de 12.5mm em 15/01 → NDVI subiu 8% em 7 dias",
    "Período seco (22/01-29/01) → Vigor estável (radar)"
  ]
}
```

**Insight Generation Logic**:
1. Detect rain events (> 10mm)
2. Calculate lag between rain and NDVI increase (typically 5-7 days)
3. Identify dry periods (> 14 days without rain)
4. Correlate NDVI changes with rain/temp patterns

### 2. Frontend: Analysis Tab

**Component**: `AnalysisTab.tsx`

**Layout**:
- **Combo Chart** (Recharts `ComposedChart`)
  - Y1 (left): Vigor (NDVI green line, RVI orange dashed)
  - Y2 (right): Rain (blue bars)
- **Insight Cards** below chart (auto-generated from API)

**UX Benefits**:
- Single view for cause-effect analysis
- Auto-generated insights reduce cognitive load
- Radar fallback visible when optical data unavailable

## Options considered

### Option A: Keep separate tabs (current approach)
**Pros**:
- No development needed
- Clean separation of concerns

**Cons**:
- Poor UX for correlation analysis
- Requires GIS expertise
- Users miss important patterns

### Option B: Correlation API + Analysis Tab (chosen)
**Pros**:
- **Single view**: All relevant data in one place
- **Auto-insights**: Reduces cognitive load
- **Proactive**: Enables early decision-making
- **Radar fallback**: Visible when optical fails

**Cons**:
- Development effort (~12h: API 6h, Frontend 6h)
- More complex API (combines 3 data sources)

### Option C: Manual correlation by user
**Pros**:
- No development needed

**Cons**:
- Requires GIS expertise
- Time-consuming
- Error-prone

## Consequences

### Positive
- **Improved UX**: Single view for correlation analysis
- **Reduced cognitive load**: Auto-generated insights
- **Proactive decisions**: Early detection of patterns
- **Competitive advantage**: Few platforms offer automated correlation

### Negative
- **Development effort**: ~12h (API: 6h, Frontend: 6h)
- **API complexity**: Combines 3 data sources (indices, radar, weather)
- **Insight accuracy**: May require calibration per region/crop

### Technical Impact

**Backend**:
- New router: `correlation_router.py` (~150 LOC)
- New service: `CorrelationService` (~150 LOC)
- Combines data from: `derived_assets`, `derived_radar_assets`, `derived_weather_daily`

**Frontend**:
- New tab: `AnalysisTab.tsx` (~100 LOC)
- New component: `CorrelationChart.tsx` (~150 LOC)
- Uses Recharts `ComposedChart` (already in dependencies)

**Database**: No schema changes (use existing tables)

### Migration Path
1. Create `correlation_router.py` + `CorrelationService`
2. Test insight generation with historical data
3. Deploy API (new route, no breaking changes)
4. Create `AnalysisTab.tsx` + `CorrelationChart.tsx`
5. Add "ANÁLISE" tab to `AOIDetailsPanel.tsx`
6. Deploy frontend (progressive enhancement)

### Validation Plan
- Test with 10+ AOIs across different regions
- Validate insight accuracy (manual review)
- Collect user feedback on usefulness
- A/B test: Analysis tab vs separate tabs

## References
- Existing tabs: `services/app-ui/src/components/AOIDetailsPanel.tsx`
- Weather API: `services/api/app/presentation/weather_router.py`
- Radar data: `services/worker/worker/jobs/process_radar.py`
- Frontend suggestions: `ai/frontend_suggestions.md`
