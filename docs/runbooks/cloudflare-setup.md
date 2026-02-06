# Cloudflare CDN Setup for VivaCampo Tiles

> Part of ADR-0007: Dynamic Tiling with MosaicJSON

## Overview

This runbook describes how to configure Cloudflare as a CDN for VivaCampo tile serving.
The CDN is **required** for acceptable production performance (cold tiles take 2-3s without cache).

## Architecture

```
┌─────────┐     ┌───────────────┐     ┌─────────┐     ┌─────────┐
│ Browser │────▶│ Cloudflare    │────▶│   API   │────▶│ TiTiler │
│         │◀────│ (Cache Layer) │◀────│         │◀────│         │
└─────────┘     └───────────────┘     └─────────┘     └─────────┘
                      │
                      ▼
               ┌─────────────┐
               │ Cache Store │
               │ (7 days)    │
               └─────────────┘
```

## Prerequisites

1. Cloudflare account with:
   - Domain added and DNS managed by Cloudflare
   - Workers enabled (free tier is sufficient for MVP)

2. Local tools:
   ```bash
   npm install -g wrangler
   wrangler login
   ```

## Option 1: Cloudflare Worker (Recommended)

Uses a Cloudflare Worker for fine-grained caching control.

### Step 1: Configure wrangler.toml

Edit `infra/cloudflare/workers/wrangler.toml`:

```toml
# Set your account ID
account_id = "your-cloudflare-account-id"

# Configure production routes
[env.production]
vars = { ORIGIN_URL = "https://api.vivacampo.com.br" }
routes = [
  { pattern = "tiles.vivacampo.com.br/*", zone_name = "vivacampo.com.br" }
]
```

### Step 2: Deploy Worker

```bash
cd infra/cloudflare/workers

# Test locally first
wrangler dev

# Deploy to staging
wrangler publish --env staging

# Deploy to production
wrangler publish --env production
```

### Step 3: Configure DNS

In Cloudflare Dashboard:
1. Go to DNS → Records
2. Add CNAME record:
   - Name: `tiles`
   - Target: `your-worker.your-subdomain.workers.dev`
   - Proxy status: Proxied (orange cloud)

### Step 4: Verify

```bash
# Test cache miss
curl -I "https://tiles.vivacampo.com.br/v1/tiles/aois/{aoi_id}/14/5920/8520.png?index=ndvi"
# Look for: CF-Cache-Status: MISS

# Test cache hit (same request)
curl -I "https://tiles.vivacampo.com.br/v1/tiles/aois/{aoi_id}/14/5920/8520.png?index=ndvi"
# Look for: CF-Cache-Status: HIT
```

---

## Option 2: Cloudflare Page Rules (Simpler)

For simpler setups without Workers.

### Step 1: Add DNS Record

1. Go to DNS → Records
2. Add A or CNAME record pointing to your API:
   - Name: `api` or `tiles`
   - Target: Your API server IP or hostname
   - Proxy status: Proxied (orange cloud)

### Step 2: Create Cache Rule

1. Go to Rules → Page Rules
2. Create rule:
   - URL pattern: `*vivacampo.com.br/v1/tiles/*`
   - Settings:
     - Cache Level: Cache Everything
     - Edge Cache TTL: 7 days
     - Browser Cache TTL: 7 days

### Step 3: Create Cache Rule for TiTiler (if exposed)

1. Create another rule:
   - URL pattern: `*vivacampo.com.br/mosaic/tiles/*`
   - Same settings as above

---

## Configuration Options

### Cache TTL

Default: 7 days (604800 seconds)

Tiles are immutable once generated (same week/AOI/index = same image).
Longer TTL reduces origin load and improves performance.

### Cache Key

The Worker caches based on:
- Full URL path
- Query parameters (sorted for consistency)

This ensures:
- Different indices (ndvi, ndre) are cached separately
- Different weeks/years are cached separately

### Bypass Conditions

The Worker passes through:
- Non-GET requests
- Non-tile URLs
- Failed responses (non-200)

---

## Monitoring

### Cloudflare Analytics

1. Go to Analytics → Workers (or Traffic)
2. Monitor:
   - Cache Hit Rate (target: >80%)
   - Request count
   - Error rate

### Custom Headers

The Worker adds these headers for debugging:

| Header | Description |
|--------|-------------|
| `CF-Cache-Status` | HIT, MISS, or BYPASS |
| `X-Cache-TTL` | Cache TTL in seconds |
| `X-VivaCampo-Cache` | Identifies our worker |

### Log Query

In Cloudflare Dashboard → Workers → Logs:

```
status:200 AND cf.cacheStatus:HIT
```

---

## Cache Warming

After deploying a new MosaicJSON or onboarding new AOIs, warm the cache:

### Option 1: WARM_CACHE Job (Recommended)

Enqueue via API or Worker:

```python
# In worker or admin script
from worker.main import enqueue_job

enqueue_job("WARM_CACHE", {
    "aoi_id": "uuid-here",
    "tenant_id": "tenant-uuid",
    "indices": ["ndvi", "ndre", "ndwi"],
    "zoom_levels": [10, 11, 12, 13, 14]
})
```

### Option 2: Manual Warming

```bash
# Warm specific tiles
for z in 10 11 12 13 14; do
  for x in $(seq 5918 5922); do
    for y in $(seq 8518 8522); do
      curl -s "https://tiles.vivacampo.com.br/v1/tiles/aois/{aoi_id}/${z}/${x}/${y}.png?index=ndvi" > /dev/null &
    done
  done
done
wait
```

---

## Troubleshooting

### Cache Not Working

1. Check DNS is proxied (orange cloud in Cloudflare)
2. Check Worker is deployed: `wrangler tail`
3. Check origin is reachable: `curl -I https://api.vivacampo.com.br/health`

### High Cache Miss Rate

1. Check if query params are consistent (no random tokens)
2. Check if tiles are unique per request (should be same for same AOI/index/week)
3. Consider pre-warming with WARM_CACHE job

### Origin Errors

1. Check API logs for 5xx errors
2. Check TiTiler logs for Planetary Computer access issues
3. Verify MosaicJSON exists in S3

### Stale Cache

To purge cache:

1. Cloudflare Dashboard → Caching → Purge Cache
2. Options:
   - Purge by URL (single tile)
   - Purge by prefix (all tiles for an AOI)
   - Purge Everything (nuclear option)

---

## Cost Estimation

### Cloudflare Workers (Free Tier)

- 100,000 requests/day free
- Sufficient for MVP with ~1000 AOIs

### Cloudflare Workers (Paid)

- $5/month for 10M requests
- Recommended for production scale

### Bandwidth

- Cloudflare: Unlimited bandwidth (included)
- Origin bandwidth: ~100KB per tile × requests

---

## Security Considerations

1. **Authentication**: Tiles require auth token, but CDN caches responses.
   - Cache key doesn't include auth header (all users share cache)
   - This is intentional: tiles are tenant-scoped by AOI ID in URL
   - AOI IDs are UUIDs, not guessable

2. **Rate Limiting**: Cloudflare provides DDoS protection.
   - Configure rate limiting rules if needed

3. **CORS**: Update API CORS to allow CDN domain:
   ```python
   CORS_ORIGINS = ["https://tiles.vivacampo.com.br", ...]
   ```

---

## Rollback

If CDN causes issues:

1. Change DNS to bypass Cloudflare (grey cloud)
2. Or disable Worker: `wrangler delete --env production`
3. Update frontend to use direct API URL

---

## Checklist

- [ ] Cloudflare account created
- [ ] Domain DNS managed by Cloudflare
- [ ] Worker deployed (`wrangler publish --env production`)
- [ ] DNS record created (tiles.vivacampo.com.br)
- [ ] Cache working (CF-Cache-Status: HIT)
- [ ] CORS configured in API
- [ ] Frontend updated to use CDN URL
- [ ] Monitoring dashboard configured
- [ ] WARM_CACHE job tested

---

## References

- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/)
- [ADR-0007: Dynamic Tiling with MosaicJSON](../adr/0007-dynamic-tiling-mosaicjson.md)
