# API Authentication - VivaCampo

Status: Draft
Last Updated: 2026-02-07

## Overview
Auth uses a session JWT returned by auth endpoints and stored in an HttpOnly `access_token` cookie.
Some endpoints also return the token in the response body.

Source: `services/api/app/presentation/auth_router.py`

## Login (Local)
`POST /v1/auth/login`

Expected:
- Request: email + password
- Response: includes `access_token` (body) and sets `access_token` cookie

## Signup (Local)
`POST /v1/auth/signup`

Expected:
- Request: email + password + tenant info (per DTO)
- Response: includes `access_token` (body) and sets `access_token` cookie

## OIDC Login
`POST /v1/auth/oidc/login`

Expected:
- Request: `id_token` + `provider`
- Response: identity + workspaces + access_token (body)

## Forgot / Reset Password
`POST /v1/auth/forgot-password`
`POST /v1/auth/reset-password`

Expected:
- Forgot returns success message
- Reset validates token and returns success message

## Workspace Switch
`POST /v1/auth/workspaces/switch`

Expected:
- Requires authenticated membership
- Returns a new session token (body)

## Token Usage
- Cookie: `access_token` (HttpOnly, SameSite=Strict, Secure based on env)
- Header usage: when needed, use `Authorization: Bearer <token>`

## Expiration & Refresh
- Session TTL: `settings.session_token_ttl_minutes` (cookie max_age derived from it)
- Refresh token endpoint: not implemented (document as not available)
