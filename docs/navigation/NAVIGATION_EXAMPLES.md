# Navigation Examples - VivaCampo

Status: Draft
Last Updated: 2026-02-07

## App UI Examples

### Public
- Landing: `http://localhost:3002/`
- Login: `http://localhost:3002/login`
- Signup: `http://localhost:3002/signup`
- Forgot Password: `http://localhost:3002/forgot-password`
- Reset Password (example): `http://localhost:3002/reset-password/abc123xyz`
- Terms: `http://localhost:3002/terms`
- Privacy: `http://localhost:3002/privacy`
- Contact: `http://localhost:3002/contact`

### Authenticated
- Dashboard: `http://localhost:3002/dashboard`
- Farms: `http://localhost:3002/farms`
- Farm Details (UUID): `http://localhost:3002/farms/123e4567-e89b-12d3-a456-426614174000`
- Signals: `http://localhost:3002/signals`
- Signal Details (UUID): `http://localhost:3002/signals/123e4567-e89b-12d3-a456-426614174000`
- Vision: `http://localhost:3002/vision`
- Vision NDVI: `http://localhost:3002/vision/ndvi`
- AI Assistant: `http://localhost:3002/ai-assistant`
- Settings (admin): `http://localhost:3002/settings`

## Admin UI Examples

- Login: `http://localhost:3001/login`
- Dashboard: `http://localhost:3001/dashboard`
- Tenants: `http://localhost:3001/tenants`
- Jobs: `http://localhost:3001/jobs`
- Missing Weeks: `http://localhost:3001/missing-weeks`
- Audit: `http://localhost:3001/audit`

## API Examples (cURL)

### Auth
```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

### List Farms
```bash
curl http://localhost:8000/v1/app/farms \
  -H "Authorization: Bearer <token>"
```

### Create Farm
```bash
curl -X POST http://localhost:8000/v1/app/farms \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Fazenda Nova","timezone":"America/Sao_Paulo"}'
```

### Get AOI Tiles (NDVI)
```bash
curl "http://localhost:8000/v1/tiles/aois/<aoi_id>/14/5000/8000.png?index=ndvi"
```
