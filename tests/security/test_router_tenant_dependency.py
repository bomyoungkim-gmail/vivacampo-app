from pathlib import Path

import pytest


EXCLUDED_ROUTERS = {"auth_router.py", "system_admin_router.py"}


@pytest.mark.security
def test_app_routers_require_tenant_dependency():
    router_dir = Path("services/api/app/presentation")
    router_files = sorted(router_dir.glob("*_router.py"))
    assert router_files, "No routers found to validate"

    violations = []
    for path in router_files:
        if path.name in EXCLUDED_ROUTERS:
            continue
        content = path.read_text(encoding="utf-8")
        if "APIRouter(" not in content:
            continue
        if "Depends(get_current_tenant_id)" not in content:
            violations.append(f"{path}: missing Depends(get_current_tenant_id) on router")

    assert not violations, "Tenant dependency missing:\n" + "\n".join(violations)
