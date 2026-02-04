# ADR-0009 — Radar-Based Harvest Detection

Date: 2026-02-04
Status: Proposed
Owners: Intelligence Team

## Context

Harvest detection is valuable for:
- **Trading companies**: Monitor crop guarantees (CPR)
- **Banks**: Track collateral status
- **Cooperatives**: Plan logistics for grain reception
- **Farmers**: Automated harvest logging

Current implementation processes Sentinel-1 radar data (VH, VV polarizations) and calculates RVI (Radar Vegetation Index). However, there's no automated harvest detection.

**Existing capabilities**:
- ✅ Sentinel-1 processing (`process_radar.py`)
- ✅ VH and VV backscatter stored in DB (`derived_radar_assets`)
- ✅ RVI calculation (`4*VH/(VV+VH)`)
- ❌ Harvest detection job - Missing

**Scientific basis**: VH backscatter drops significantly (> 3dB) when crops are harvested because bare soil reflects less radar energy than standing vegetation.

## Decision

Create `DETECT_HARVEST` worker job that:
1. Compares VH backscatter (current week vs previous week)
2. If drop > 3dB, creates `HARVEST_DETECTED` signal
3. Stores VH values in signal metadata for audit trail

**Algorithm**:
```python
current_vh = get_vh_mean(aoi_id, days_ago=0)
previous_vh = get_vh_mean(aoi_id, days_ago=7)

if (current_vh - previous_vh) < -3.0:  # 3dB drop
    create_signal(
        type="HARVEST_DETECTED",
        severity="INFO",
        metadata={"vh_current": current_vh, "vh_previous": previous_vh}
    )
```

**Trigger**: Run weekly after `PROCESS_RADAR_WEEK` completes.

## Options considered

### Option A: Optical-only detection (NDVI drop)
**Pros**:
- Simpler (reuse existing NDVI data)

**Cons**:
- Fails in cloudy conditions (common during harvest season)
- NDVI drops for many reasons (drought, disease, not just harvest)
- Less reliable

### Option B: Radar-based detection (chosen)
**Pros**:
- **All-weather**: Works through clouds
- **Specific signal**: VH drop is highly correlated with harvest
- **Automated**: No manual reporting needed
- **Audit trail**: VH values stored in metadata

**Cons**:
- Requires Sentinel-1 data (already processed)
- 3dB threshold may need calibration per crop type

### Option C: Manual harvest reporting
**Pros**:
- No development needed

**Cons**:
- Unreliable (farmers forget to report)
- Delayed (days or weeks after actual harvest)
- Not scalable

## Consequences

### Positive
- **Automated detection**: No manual input required
- **All-weather**: Works when optical satellites can't
- **Financial monitoring**: Banks/traders can track guarantees
- **Logistics planning**: Cooperatives can prepare for grain reception
- **Audit trail**: VH values provide proof of detection

### Negative
- **False positives**: Heavy rain or flooding can cause VH drop
- **Calibration needed**: 3dB threshold may vary by crop type
- **Development effort**: ~3h (job creation + testing)

### Technical Impact
- **Worker**: New job `detect_harvest.py` (~100 LOC)
- **Database**: Use existing `opportunity_signals` table
- **API**: No changes (signals already exposed via `/v1/signals`)
- **Frontend**: Harvest signals appear in Alerts tab (no changes needed)

### Migration Path
1. Create `detect_harvest.py` job handler
2. Register job type in worker dispatcher
3. Schedule weekly execution (after radar processing)
4. Monitor false positive rate
5. Calibrate threshold if needed (per crop type)

### Validation Plan
- Test with known harvest dates (historical data)
- Monitor false positive rate (target < 10%)
- Collect user feedback on accuracy

## References
- Existing radar processing: `services/worker/worker/jobs/process_radar.py`
- VH backscatter research: "Sentinel-1 for Crop Monitoring" (ESA)
- Signal system: `services/api/app/presentation/signals_router.py`
