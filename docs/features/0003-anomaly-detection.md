# FEAT-0003 — Anomaly Detection and Signals

Date: 2026-01-15
Owner: Backend Team, AI Team
Status: Done

## Goal
Automatically detect agricultural anomalies (crop stress, water issues, pest risk) from satellite data and alert users with actionable insights.

**User value:** Users receive proactive alerts about field problems before they become visible to the naked eye, enabling early intervention.

## Scope
**In scope:**
- Change detection between consecutive weeks (NDVI drop >10%)
- Multi-index anomaly scoring (NDVI, NDRE, NDWI combined)
- Severity classification (LOW, MEDIUM, HIGH, CRITICAL)
- Signal types: CHANGE_DETECTED, ANOMALY, ALERT, PASTURE_FORAGE_RISK, CROP_STRESS, PEST_OUTBREAK
- Recommended actions generation
- Signal history and trends

**Out of scope:**
- Push notifications (email/SMS) - planned for FEAT-0020
- Prescription map generation (agronomist responsibility)
- Real-time alerts (<1 day latency)

## User Stories
- **As a farmer**, I want to be alerted when crop health drops significantly, so that I can investigate the field early.
- **As an agronomist**, I want to see confidence scores and evidence, so that I can prioritize field visits.
- **As a farm manager**, I want to view all active signals across farms, so that I can coordinate response efforts.

## UX Notes
**Signal Card States:**
- **New signal:** Yellow highlight, "NEW" badge
- **Acknowledged:** Normal display
- **Resolved:** Grayed out, strikethrough

**Signal Details:**
- Severity badge (color-coded: green/yellow/orange/red)
- Affected area (polygon highlight on map)
- Confidence percentage
- Evidence JSON (index values, historical comparison)
- Recommended actions list

**Signal List Filters:**
- By signal type
- By severity
- By date range
- By farm/AOI

## Contract Changes
**API:**
- Endpoint: `GET /v1/aois/{aoi_id}/signals`
- Response:
  ```json
  {
    "signals": [
      {
        "id": "uuid",
        "signal_type": "CROP_STRESS",
        "severity": "HIGH",
        "confidence": 0.87,
        "detected_at": "2026-01-20T00:00:00Z",
        "evidence_json": {
          "ndvi_drop": -0.15,
          "ndwi_drop": -0.08,
          "affected_area_ha": 12.3
        },
        "recommended_action": "Verificar irrigacao na area afetada",
        "recommended_actions": [
          "Verificar irrigacao na area afetada",
          "Coletar amostras de solo",
          "Consultar agronomo"
        ]
      }
    ]
  }
  ```

**Domain:**
- Entity: `OpportunitySignal` with `signal_type`, `severity`, `confidence`, `evidence_json`
- Service: `detect_anomalies(aoi_id, week_date)` - runs after weekly processing
- AI Copilot: Generates `recommended_actions` based on signal type and evidence

**Data:**
- Table: `opportunity_signals`
- Columns: `id`, `aoi_id`, `signal_type`, `severity`, `confidence`, `evidence_json`, `recommended_actions`, `detected_at`, `acknowledged_at`, `resolved_at`

## Acceptance Criteria
- [x] System detects NDVI drops >10% week-over-week
- [x] System classifies severity based on drop magnitude and affected area
- [x] System generates confidence scores (0-1)
- [x] User sees signals in AOI details panel
- [x] User sees signal markers on map
- [x] AI Copilot generates recommended actions
- [x] Signal history is preserved for trend analysis

## Observability
**Logs:**
- `signal.detected` (aoi_id, signal_type, severity, confidence)
- `signal.acknowledged` (signal_id, user_id)
- `anomaly.analysis_completed` (aoi_id, signals_count)

**Metrics:**
- `signals_detected_total` (counter by signal_type, severity)
- `anomaly_detection_duration_seconds` (histogram)

## Testing
**Unit tests:**
- Change detection algorithm (various NDVI patterns)
- Severity classification logic
- Confidence score calculation

**Integration tests:**
- End-to-end: Weekly processing -> Signal detection -> API retrieval
- Signal filtering and pagination

## Status
Done - Deployed 2026-01-20
