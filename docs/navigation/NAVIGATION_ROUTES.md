# Navigation Routes - VivaCampo

Status: Draft
Last Updated: 2026-02-07

## Notes
- Base paths are not used in the app UI (legacy `/app` removed).
- Routes listed here are derived from the Next.js `src/app` folders and navigation configs.
- API routes use `/v1` as the current version prefix.

## App UI Routes (services/app-ui)

| Label | Route | Access | Notes |
| --- | --- | --- | --- |
| Home | `/` | Public | Landing page |
| Login | `/login` | Public | Auth UI |
| Signup | `/signup` | Public | Auth UI |
| Forgot Password | `/forgot-password` | Public | Auth UI |
| Reset Password | `/reset-password/[token]` | Public | Dynamic |
| Terms | `/terms` | Public | Legal |
| Privacy | `/privacy` | Public | Legal |
| Contact | `/contact` | Public | Landing |
| Dashboard | `/dashboard` | Authenticated | Main nav |
| Farms | `/farms` | Authenticated | Main nav |
| Farm Details | `/farms/[id]` | Authenticated | Dynamic |
| Signals | `/signals` | Authenticated | Main nav |
| Signal Details | `/signals/[id]` | Authenticated | Dynamic |
| Vision | `/vision` | Authenticated | Main nav |
| Vision Details | `/vision/[type]` | Authenticated | Dynamic |
| AI Assistant | `/ai-assistant` | Authenticated | Main nav |
| Settings | `/settings` | Tenant Admin / System Admin | Role protected |
| Map Embed | `/map-embed` | Authenticated | Embed map UI |

## Dynamic Routes (App UI)

| Route | Params | Type | Example | Description |
| --- | --- | --- | --- | --- |
| `/farms/[id]` | `id` | UUID | `/farms/123e4567-e89b-12d3-a456-426614174000` | Farm details page |
| `/signals/[id]` | `id` | UUID | `/signals/123e4567-e89b-12d3-a456-426614174000` | Signal details page |
| `/vision/[type]` | `type` | string | `/vision/ndvi` | Vision analysis by type |
| `/reset-password/[token]` | `token` | string | `/reset-password/abc123xyz` | Password reset |

## Admin UI Routes (services/admin-ui)

| Label | Route | Access | Notes |
| --- | --- | --- | --- |
| Root | `/` | System Admin | Admin root |
| Login | `/login` | Public | Admin auth |
| Dashboard | `/dashboard` | System Admin | Admin nav |
| Tenants | `/tenants` | System Admin | Admin nav |
| Jobs | `/jobs` | System Admin | Admin nav |
| Missing Weeks | `/missing-weeks` | System Admin | Admin nav |
| Audit | `/audit` | System Admin | Admin nav |

## API Routes (services/api)

### Core

| Label | Route | Notes |
| --- | --- | --- |
| Root | `/` | API root |
| Health | `/health` | Health check |
| Metrics | `/metrics` | Prometheus-style metrics |
| OpenAPI | `/docs` | Swagger UI |
| ReDoc | `/redoc` | ReDoc UI |

### Router Prefixes

| Tag | Prefix | Notes |
| --- | --- | --- |
| auth | `/v1` | Auth endpoints |
| farms | `/v1/app` | Farms |
| aois | `/v1/app` | AOIs |
| jobs | `/v1/app` | Jobs |
| signals | `/v1/app` | Signals |
| weather | `/v1/app` | Weather |
| radar | `/v1/app` | Radar |
| nitrogen | `/v1/app` | Nitrogen |
| correlation | `/v1/app` | Correlation |
| analytics | `/v1/app` | Analytics |
| ai-assistant | `/v1/app` | AI Assistant |
| tenant-admin | `/v1/app` | Tenant admin |
| system-admin | `/v1` | System admin |
| tiles | `/v1` | Tiles |
