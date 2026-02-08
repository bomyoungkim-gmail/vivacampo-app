# API Endpoints - VivaCampo (High-Level)

Status: Draft
Last Updated: 2026-02-07

Source of truth: OpenAPI `/docs`

## Auth (`/v1`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| POST | `/v1/auth/signup` | Public | Local signup |
| POST | `/v1/auth/login` | Public | Local login |
| POST | `/v1/auth/forgot-password` | Public | Request reset |
| POST | `/v1/auth/reset-password` | Public | Reset password |
| POST | `/v1/auth/oidc/login` | Public | OIDC login |
| POST | `/v1/auth/workspaces/switch` | Auth | Switch tenant |
| GET | `/v1/me` | Auth | Not implemented |

## Farms (`/v1/app`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/v1/app/farms` | Auth | List farms |
| POST | `/v1/app/farms` | EDITOR | Create farm |
| GET | `/v1/app/farms/geocode` | Auth | Geocode proxy |

## AOIs (`/v1/app`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/v1/app/aois` | Auth | List AOIs |
| POST | `/v1/app/aois` | EDITOR | Create AOI |
| PATCH | `/v1/app/aois/{aoi_id}` | EDITOR | Update AOI |
| DELETE | `/v1/app/aois/{aoi_id}` | EDITOR | Delete AOI |
| POST | `/v1/app/aois/{aoi_id}/backfill` | EDITOR | Request backfill |
| GET | `/v1/app/aois/{aoi_id}/assets` | Auth | Latest assets |
| GET | `/v1/app/aois/{aoi_id}/history` | Auth | History |
| POST | `/v1/app/aois/status` | Auth | Batch status |
| POST | `/v1/app/aois/simulate-split` | TENANT_ADMIN | Simulate split |
| POST | `/v1/app/aois/split` | TENANT_ADMIN | Persist split |

## Jobs (`/v1/app`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/v1/app/jobs` | Auth | List jobs |
| GET | `/v1/app/jobs/{job_id}` | Auth | Job details |
| GET | `/v1/app/jobs/{job_id}/runs` | Auth | Run history |
| POST | `/v1/app/jobs/{job_id}/retry` | EDITOR | Retry job |
| POST | `/v1/app/jobs/{job_id}/cancel` | EDITOR | Cancel job |

## Signals (`/v1/app`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/v1/app/signals` | Auth | List signals |
| GET | `/v1/app/signals/{signal_id}` | Auth | Signal details |
| POST | `/v1/app/signals/{signal_id}/ack` | Auth | Acknowledge |

## Weather (`/v1/app`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/v1/app/aois/{aoi_id}/weather/history` | Auth | Weather history |
| POST | `/v1/app/aois/{aoi_id}/weather/sync` | EDITOR | Trigger sync |

## Radar (`/v1/app`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/v1/app/aois/{aoi_id}/radar/history` | Auth | Radar history |

## Nitrogen (`/v1/app`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/v1/app/aois/{aoi_id}/nitrogen/status` | Auth | Nitrogen status |

## Correlation (`/v1/app`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/v1/app/aois/{aoi_id}/correlation/vigor-climate` | Auth | Correlation |
| GET | `/v1/app/aois/{aoi_id}/correlation/year-over-year` | Auth | YoY NDVI |

## Analytics (`/v1/app`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| POST | `/v1/app/field-data` | TENANT_ADMIN | Field calibration |
| GET | `/v1/app/analytics/calibration` | TENANT_ADMIN | Calibration model |
| GET | `/v1/app/analytics/prediction` | TENANT_ADMIN | Prediction |
| POST | `/v1/app/field-feedback` | TENANT_ADMIN | Field feedback |

## AI Assistant (`/v1/app`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| POST | `/v1/app/ai-assistant/threads` | Auth | Create thread |
| GET | `/v1/app/ai-assistant/threads` | Auth | List threads |
| POST | `/v1/app/ai-assistant/threads/{thread_id}/messages` | Auth | Send message |
| GET | `/v1/app/ai-assistant/threads/{thread_id}/messages` | Auth | List messages |
| GET | `/v1/app/ai-assistant/approvals` | Auth | List approvals |
| POST | `/v1/app/ai-assistant/approvals/{approval_id}/decide` | EDITOR | Decide |

## Tenant Admin (`/v1/app`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/v1/app/admin/tenant/members` | TENANT_ADMIN | List members |
| POST | `/v1/app/admin/tenant/members/invite` | TENANT_ADMIN | Invite |
| PATCH | `/v1/app/admin/tenant/members/{membership_id}/role` | TENANT_ADMIN | Update role |
| PATCH | `/v1/app/admin/tenant/members/{membership_id}/status` | TENANT_ADMIN | Update status |
| GET | `/v1/app/admin/tenant/settings` | TENANT_ADMIN | Get settings |
| PATCH | `/v1/app/admin/tenant/settings` | TENANT_ADMIN | Update settings |
| GET | `/v1/app/admin/tenant/audit` | TENANT_ADMIN | Tenant audit |

## System Admin (`/v1`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/v1/admin/tenants` | SYSTEM_ADMIN | List tenants |
| POST | `/v1/admin/tenants` | SYSTEM_ADMIN | Create tenant |
| PATCH | `/v1/admin/tenants/{tenant_id}` | SYSTEM_ADMIN | Update tenant |
| GET | `/v1/admin/jobs` | SYSTEM_ADMIN | List jobs |
| POST | `/v1/admin/jobs/{job_id}/retry` | SYSTEM_ADMIN | Retry job |
| POST | `/v1/admin/jobs/reprocess` | SYSTEM_ADMIN | Reprocess |
| POST | `/v1/admin/ops/reprocess-missing-aois` | SYSTEM_ADMIN | Backfill missing |
| GET | `/v1/admin/ops/missing-weeks` | SYSTEM_ADMIN | List missing |
| POST | `/v1/admin/ops/reprocess-missing-weeks` | SYSTEM_ADMIN | Reprocess missing |
| GET | `/v1/admin/ops/health` | SYSTEM_ADMIN | System health |
| GET | `/v1/admin/ops/queues` | SYSTEM_ADMIN | Queue stats |
| GET | `/v1/admin/audit` | SYSTEM_ADMIN | Global audit |
| GET | `/v1/admin/providers/status` | SYSTEM_ADMIN | Providers |

## Tiles (`/v1`)

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/v1/tiles/aois/{aoi_id}/{z}/{x}/{y}.png` | Auth | Tile PNG |
| GET | `/v1/tiles/aois/{aoi_id}/tilejson.json` | Auth | TileJSON |
| GET | `/v1/tiles/aois/{aoi_id}/export/status` | Auth | Export status |
| POST | `/v1/tiles/aois/{aoi_id}/export` | Auth | Export COG |
| GET | `/v1/tiles/config` | Public | Tile config |
| GET | `/v1/tiles/indices` | Public | Available indices |
