# ADR-0008 — SRRE Index and Nitrogen Detection

Date: 2026-02-04
Status: Proposed
Owners: Intelligence Team

## Context

Current implementation has 13 vegetation indices but lacks SRRE (Simple Ratio Red Edge), which recent research (IEEE 2024) shows has superior correlation (R² > 0.8) for nitrogen absorption in corn and rice compared to NDRE.

Nitrogen deficiency is a critical agronomic issue that affects crop yield. Early detection enables variable rate nitrogen application, reducing costs and environmental impact.

**Existing capabilities**:
- ✅ NDRE (Normalized Difference Red Edge) - `(B08-B05)/(B08+B05)`
- ✅ RECI (Red Edge Chlorophyll Index) - `(B08/B05)-1`
- ✅ GNDVI, EVI, other vegetation indices
- ❌ SRRE - Missing

**Detection pattern**: High NDVI (> 0.7) + Low NDRE (< 0.5) + Low RECI (< 1.5) indicates nitrogen deficiency.

## Decision

1. **Add SRRE index** to `services/tiler/tiler/expressions.py`
   - Formula: `B08 / B05` (simpler than NDRE, better correlation)
   - Rescale: `0.5,8`
   - Colormap: `rdylgn` (red-yellow-green)

2. **Create Nitrogen Detection API** at `/v1/aois/{aoi_id}/nitrogen/status`
   - Algorithm: Compare NDVI, NDRE, RECI thresholds
   - Response: Status (DEFICIENT/ADEQUATE/UNKNOWN), confidence, recommendation
   - Zone map URL for variable rate application

3. **Frontend component**: `NitrogenAlert.tsx`
   - Yellow alert card when deficiency detected
   - Show NDVI vs NDRE comparison
   - Button to view zone map (TiTiler tile layer)

## Options considered

### Option A: Use only NDRE (current approach)
**Pros**:
- Already implemented
- Well-known index

**Cons**:
- Lower correlation for nitrogen (R² ~0.6-0.7 vs SRRE's R² > 0.8)
- Less accurate for variable rate recommendations

### Option B: Implement SRRE + Detection API (chosen)
**Pros**:
- Higher accuracy (R² > 0.8 for corn/rice)
- Simpler formula (`B08/B05` vs normalized difference)
- Enables precision agriculture (variable rate N)
- Research-backed (IEEE 2024 papers)

**Cons**:
- New index to maintain
- Requires API development (~100 LOC)

### Option C: Manual agronomist analysis
**Pros**:
- No development needed

**Cons**:
- Not scalable
- Delayed response
- Inconsistent across users

## Consequences

### Positive
- **Improved accuracy**: R² > 0.8 for nitrogen detection
- **Cost savings**: Variable rate application reduces fertilizer waste
- **Environmental impact**: Less nitrogen runoff
- **Competitive advantage**: Few platforms offer automated nitrogen detection

### Negative
- **Development effort**: ~8h (SRRE: 5 min, API: 4h, Frontend: 3h)
- **Maintenance**: One more index to support
- **Validation needed**: Requires field testing to confirm accuracy

### Technical Impact
- **Backend**: Add 5 lines to `expressions.py`
- **API**: New router `nitrogen_router.py` (~100 LOC)
- **Frontend**: New component `NitrogenAlert.tsx` (~80 LOC)
- **Database**: No schema changes (use existing `derived_assets` table)

### Migration Path
1. Add SRRE to `expressions.py` (backward compatible)
2. Deploy TiTiler (no downtime)
3. Create API endpoint (new route, no breaking changes)
4. Deploy frontend component (progressive enhancement)

## References
- IEEE 2024: "SRRE for Nitrogen Detection in Corn and Rice"
- Existing indices: `services/tiler/tiler/expressions.py`
- Detection logic: `intelligence_capabilities.md`
