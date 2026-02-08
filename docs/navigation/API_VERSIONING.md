# API Versioning - VivaCampo

Status: Draft
Last Updated: 2026-02-07

## Current Version
- `v1` is the current stable API version.

## Policy
- Breaking changes require a new major version (e.g., `/v2`).
- Backward-compatible additions remain in the current major version.
- Deprecations should provide a transition window (recommended: 6 months).

## Deprecation Communication
- Add response header: `X-API-Deprecated: true` for deprecated endpoints.
- Document migration guidance in release notes or a dedicated migration doc.

## Notes
- No `/v2` currently exists.
