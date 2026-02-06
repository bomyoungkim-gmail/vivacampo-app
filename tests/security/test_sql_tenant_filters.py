import re
from pathlib import Path

import pytest


TENANT_TABLES = {
    "farms",
    "aois",
    "aoi_versions",
    "jobs",
    "job_runs",
    "observations_weekly",
    "derived_assets",
    "alerts",
    "seasons",
    "yield_forecasts",
    "tenant_webhooks",
    "tenant_event_outbox",
    "opportunity_signals",
    "signal_feedback",
    "copilot_threads",
    "copilot_checkpoints",
    "copilot_approvals",
    "derived_radar_assets",
    "derived_weather_daily",
    "derived_topography",
}

SQL_TEXT_PATTERN = re.compile(r"text\(\s*\"\"\"(.*?)\"\"\"", re.DOTALL | re.IGNORECASE)


@pytest.mark.security
def test_raw_sql_in_repositories_enforces_tenant_filter():
    repo_dir = Path("services/api/app/infrastructure/adapters/persistence/sqlalchemy")
    files = sorted(repo_dir.glob("*.py"))
    assert files, "No repository files found to validate"

    violations = []
    for path in files:
        if path.name in {"system_admin_repository.py"}:
            continue
        content = path.read_text(encoding="utf-8")
        for match in SQL_TEXT_PATTERN.finditer(content):
            sql = match.group(1)
            lower = sql.lower()
            if not any(f"from {table}" in lower for table in TENANT_TABLES):
                continue
            if "tenant_id" not in lower:
                violations.append(f"{path}: missing tenant_id filter in SQL block: {sql.strip()}")

    assert not violations, "Tenant filter missing:\n" + "\n".join(violations)
