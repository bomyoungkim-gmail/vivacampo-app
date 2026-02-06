# ADR-0006 — Presigned URLs for TiTiler Security

Date: 2026-01-25
Status: Accepted
Owners: Backend Team, Infrastructure Team

## Context
VivaCampo uses TiTiler to serve satellite imagery (GeoTIFFs stored in S3) as XYZ map tiles. The original implementation exposed raw S3 URIs in API responses:

```
GET /cog/tiles/{z}/{x}/{y}?url=s3://vivacampo-rasters/aoi_123/ndvi.tif
```

**Security concerns:**
- S3 bucket name exposed in client-side code
- Users could potentially enumerate other AOI data
- No access control on tile requests
- Potential for unauthorized data access

**Requirements:**
- Hide S3 bucket/key structure from clients
- Enforce tenant isolation (users can only access their AOIs)
- Support tile caching (CDN-friendly)
- Minimal latency impact

## Decision
**Use presigned URLs for TiTiler requests** with short expiration (1 hour).

## Options considered

### 1) Public S3 bucket
**Pros:**
- Simple implementation
- Fast (direct S3 access)

**Cons:**
- No security - anyone can access all data
- S3 bucket exposed
- Violates multi-tenant isolation
- **Rejected immediately**

### 2) API proxy all tile requests
**Pros:**
- Full control over access
- Can enforce tenant isolation

**Cons:**
- High latency (every tile through API)
- API becomes bottleneck
- Cannot leverage CDN caching effectively
- Expensive at scale

### 3) S3 presigned URLs ✅
**Pros:**
- S3 keys hidden from clients
- Time-limited access (1 hour expiration)
- Client talks directly to S3/TiTiler after initial auth
- CDN-cacheable (within expiration window)
- No API bottleneck for tiles

**Cons:**
- Slightly more complex API response
- URLs expire (must refresh)
- Cannot revoke access immediately (must wait for expiration)

### 4) CloudFront signed URLs/cookies
**Pros:**
- Similar to presigned URLs
- Better CDN integration

**Cons:**
- Requires CloudFront setup (not yet deployed)
- More complex key management
- Over-engineering for current stage

## Consequences
**What changes:**
- API returns presigned URLs instead of raw S3 URIs
- Frontend uses presigned URL in TiTiler requests
- URLs expire after 1 hour (configurable)
- Refresh mechanism for long sessions

**Implementation:**
```python
# API response
{
  "tile_url": "https://tiler.vivacampo.com/cog/tiles/{z}/{x}/{y}?url=https://s3.amazonaws.com/vivacampo-rasters/aoi_123/ndvi.tif?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...&X-Amz-Expires=3600&X-Amz-Signature=..."
}
```

```python
# Backend (services/api/app/infrastructure/webhooks.py)
def generate_presigned_tile_url(s3_uri: str, expires_in: int = 3600) -> str:
    bucket, key = parse_s3_uri(s3_uri)
    presigned = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=expires_in
    )
    return f"{TILER_BASE_URL}/cog/tiles/{{z}}/{{x}}/{{y}}?url={quote(presigned)}"
```

**Security guarantees:**
- Tenant isolation: API validates `tenant_id` before generating presigned URL
- Time-limited: URLs expire after 1 hour
- No enumeration: S3 keys not exposed to clients
- Audit trail: API logs who requested which tiles

**Trade-offs accepted:**
- URLs expire - **mitigated by:**
  - 1 hour is sufficient for typical session
  - Frontend refreshes URLs on map interaction
  - Background refresh before expiration
- Cannot revoke immediately - **mitigated by:**
  - 1 hour max exposure
  - Can rotate AWS credentials in emergency
  - Monitoring for abuse

## Follow-ups
- [x] Implement presigned URL generation in API
- [x] Update frontend to use presigned URLs
- [x] Add URL refresh mechanism for long sessions
- [x] Add integration tests for presigned URL flow
- [ ] Monitor presigned URL usage patterns (TASK-0275)
- [ ] Consider CloudFront signed cookies for production (TASK-0280)
