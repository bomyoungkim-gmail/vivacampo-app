# Navigation Flows - VivaCampo

Status: Draft
Last Updated: 2026-02-07

## App UI - Authentication & Redirects

Source: `services/app-ui/src/middleware.ts`

### Public routes
- `/`
- `/login`
- `/signup`
- `/forgot-password`
- `/reset-password`
- `/terms`
- `/privacy`
- `/contact`

### Redirect rules
- Any non-public route without `access_token` cookie -> redirect to `/login?redirect={path}`
- `/login` or `/signup` with `access_token` cookie -> redirect to `/dashboard`
- Role protected:
  - `/settings` requires `tenant_admin` or `system_admin` (decoded from JWT)
  - `/admin` requires `system_admin` (note: App UI does not define `/admin` pages; keep for safety)

### Landing behavior
- `/` always renders the landing page (no auto-redirect when authenticated)

## App UI - Key flows

### Login flow
1. User accesses `/login`
2. On success, `access_token` cookie is set
3. User is redirected to `/dashboard` (or stays if client code handles redirect)

### Signup flow
1. User accesses `/signup`
2. On success, `access_token` cookie is set
3. User is redirected to `/dashboard`

### Forgot/Reset flow
1. `/forgot-password` triggers reset token delivery
2. `/reset-password/[token]` completes reset

## Admin UI - Authentication notes

Source: `services/admin-ui/src/components/AdminSidebar.tsx`

- Admin UI uses `admin_token` in `localStorage` for logout.
- There is no admin middleware file in `services/admin-ui` (confirm if added elsewhere).
- All admin routes should be considered `system_admin` only (see nav list in sidebar).
