# Missing Critical Tests

## Status
- **Severity P0 – RBAC/tenant isolation enforcement (now covered):** `tests/test_rbac.py` adds `VIEWER` vs. `EDITOR` enforcement plus a cross-tenant backfill attempt. That file now exercises the negative paths that were previously missing, so the multi-tenant security boundary is backstopped by tests.
- **Severity P1 – Core job handler execution/resilience (now covered with controlled stubs):** `tests/test_worker_jobs.py` drives `BACKFILL`, `PROCESS_WEEK`, `ALERTS_WEEK`, `SIGNALS_WEEK`, and `FORECAST_WEEK` handlers. External I/O (SQS + heavy processing) is stubbed so we can assert job status transitions and DB side effects deterministically.
- **Severity P2 – External integration coverage (now covered with stubs):** `tests/test_integrations_p2.py` validates STAC client mapping, webhook outbox delivery, and AI provider factory behavior using controlled stubs.
- Remaining gaps below remain open.

## Outstanding
None.
