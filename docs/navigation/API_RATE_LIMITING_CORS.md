# API Rate Limiting & CORS - VivaCampo

Status: Draft
Last Updated: 2026-02-07

## Rate Limiting

Source: `services/api/app/main.py` + `app.middleware.rate_limit`

- Global rate limiting is enforced via SlowAPI.
- Default behavior: returns HTTP 429 with standard error shape.

Expected response on limit exceeded:
```json
{
  "error": {
    "code": "TOO_MANY_REQUESTS",
    "message": "Rate limit exceeded",
    "details": {"limit": "..."},
    "traceId": "..."
  }
}
```

### Headers
If enabled by middleware, standard headers may include:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

## CORS

Source: `services/api/app/main.py`

### Local environment
- Allowed origins:
  - `http://localhost:3000`
  - `http://localhost:3001`
  - `http://localhost:3002`
- Allowed methods: `GET`, `POST`, `PATCH`, `DELETE`
- Credentials: enabled
- Allowed headers: `*`

### Non-local environments
- `allow_origins` is empty by default (configure via env or deploy config)
