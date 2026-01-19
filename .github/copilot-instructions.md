<!-- Copilot instructions for vivacampo-app -->
# Copilot / AI Contributor Quick Guide

Purpose: give AI coding agents the minimal, actionable knowledge to be productive in this repository.

Primary source: `BoasPraticas.txt` at repository root contains the canonical frontend/backend rules. Read it before changing architecture.

Big picture
- This repo follows a two-part architecture described in `BoasPraticas.txt`:
  - Frontend: React 18 + TypeScript with clear separation between UI, domain/use-cases and services.
  - Backend/service: Node.js + TypeScript with layered boundaries (presentation -> application -> domain -> infrastructure).

Key conventions (use these exactly)
- Frontend:
  - UI components must be presentation-only. Business logic lives in `domain`/`use-cases` or `hooks/domain`.
  - Hooks directories are separated by purpose: `hooks/ui`, `hooks/data`, `hooks/domain`.
  - HTTP clients/adapters live under `services/api` (interceptors, auth refresh, retries); avoid fetch/axios calls scattered in components.
  - Avoid deep relative imports across features; expose public entrypoints for each feature and prefer `shared/types` for cross-cutting types.
- Backend:
  - Controllers/handlers are thin: validate, auth, map DTOs, invoke a use-case; never place business logic in controllers.
  - Use-cases (application) orchestrate repos/services and handle transactions.
  - Domain contains pure entities, value objects and invariants; domain must not import infrastructure/frameworks.
  - Infrastructure implements ports/interfaces from application/domain (ORM, queues, external APIs).

Developer workflows (what to check first)
- This repository currently lacks `package.json` and common config files in the repo root; before running builds/tests, locate the service or frontend subfolders (look for `api/`, `package.json`, `tsconfig.json`).
- If you find `package.json` in a folder, prefer `npm ci` (or `pnpm install` / `yarn --frozen-lockfile` if lockfile present) then run the repo-local scripts (e.g. `npm run lint`, `npm run build`, `npm test`). If scripts are missing, ask the user for intended commands.

Patterns to preserve when editing
- Preserve import boundaries: presentation -> application -> domain -> infrastructure. Do not let controllers call ORM directly.
- Break circular deps by extracting interfaces/types to `shared` or creating explicit adapter entrypoints.
- Keep utilities small and cohesive (avoid a single large `utils` bag).

Integration points to verify
- PostgreSQL + ORM (Prisma) and migrations/seeds are the expected DB setup — if you modify persistence, ensure migrations and idempotent seeds exist.
- External integrations (email, storage, queues) should be implemented in `infrastructure` and invoked via well-defined ports.

Documentation pointers for PRs
- Reference `BoasPraticas.txt` when your change touches architecture or boundaries.
- For refactors, target small PRs that address one priority (P0/P1/P2) as defined in `BoasPraticas.txt`.

If anything is missing
- I could not detect package/config files in the repo root. Tell me where the frontend/backend subfolders and build/test scripts live, or allow me to search for `package.json`/`api/` subfolders and update these instructions.

Next step: after you confirm where the code lives and toolchain commands, I will merge or refine this guidance with concrete build/test commands and file examples.
