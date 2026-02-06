from pathlib import Path
import re

import pytest


ROUTE_DECORATOR = re.compile(r"^@router\.(get|post|patch|delete|put)\(", re.IGNORECASE)


@pytest.mark.security
def test_system_admin_router_requires_guard():
    path = Path("services/api/app/presentation/system_admin_router.py")
    content = path.read_text(encoding="utf-8").splitlines()

    violations = []
    i = 0
    while i < len(content):
        line = content[i].strip()
        if ROUTE_DECORATOR.match(line):
            # Scan forward to function signature
            j = i + 1
            signature_lines = []
            while j < len(content):
                signature_lines.append(content[j])
                if content[j].strip().endswith("):"):
                    break
                j += 1
            signature_blob = "\n".join(signature_lines)
            if "Depends(get_current_system_admin)" not in signature_blob:
                violations.append(f"{path}: missing get_current_system_admin in route near line {i + 1}")
            i = j
        i += 1

    assert not violations, "System admin guard missing:\n" + "\n".join(violations)
