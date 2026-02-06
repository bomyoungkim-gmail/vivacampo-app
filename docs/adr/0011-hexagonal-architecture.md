# ADR-0011 — Adopt Hexagonal Architecture (Ports & Adapters)

Date: 2026-02-06
Status: Accepted
Owners: Platform

## Context

The codebase had business logic spread across routers, jobs, and ad-hoc services. This made unit testing difficult, increased coupling to frameworks, and raised the risk of tenant data leakage due to inconsistent filtering.

We needed a consistent architecture that:
- Enforces dependency direction (domain isolated from frameworks)
- Improves testability (use cases with port fakes)
- Standardizes adapter wiring (DI containers)
- Supports multi-tenant controls and RLS context

## Decision

Adopt a hexagonal architecture (Ports & Adapters) across API and worker services:

1. **Presentation layer**: FastAPI routers and job handlers are thin and delegate to use cases.
2. **Application layer**: Use cases + DTOs (commands/responses) orchestrate domain rules and ports.
3. **Domain layer**: Entities/value objects and ports are framework-agnostic (no FastAPI/SQLAlchemy types).
4. **Infrastructure layer**: Adapters implement ports (DB, queues, storage, external providers).
5. **Dependency injection**: Central DI container resolves adapters per environment and supports test overrides.

## Consequences

### Positive
- Consistent separation of concerns across services
- Testable use cases without infrastructure
- Easier to swap adapters (LocalStack vs AWS, mock providers)
- Clear enforcement of tenant isolation patterns

### Negative
- Increased file count and boilerplate
- DI wiring adds initial complexity
- Requires discipline to keep routers/jobs thin

## Implementation Status
- ✅ Phases 1–6 implemented (domain, infrastructure, application, DI, presentation, worker jobs)
- ⏳ Phase 7 pending (E2E + validation)
- ✅ Phase 8 cleanup completed (legacy paths removed)

## References
- `ai/HEXAGONAL_EXECUTION_PLAN.md`
- `ai/HEXAGONAL_ARCHITECTURE_PLAN.md`
