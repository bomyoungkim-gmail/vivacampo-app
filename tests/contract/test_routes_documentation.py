import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_route_docs import _walk_app_routes, _collect_api_endpoints


RE_BACKTICK_ROUTE = re.compile(r"`(/[^`]*)`")


def _extract_doc_routes(doc_path: Path) -> set[str]:
    content = doc_path.read_text(encoding="utf-8")
    return {match.group(1) for match in RE_BACKTICK_ROUTE.finditer(content)}


def test_app_and_admin_routes_documented():
    repo_root = Path(__file__).resolve().parents[2]
    app_ui_root = repo_root / "services" / "app-ui" / "src" / "app"
    admin_ui_root = repo_root / "services" / "admin-ui" / "src" / "app"
    doc_path = repo_root / "ai" / "NAVIGATION_ROUTES.md"

    app_routes = set(_walk_app_routes(app_ui_root))
    admin_routes = set(_walk_app_routes(admin_ui_root))
    documented_routes = _extract_doc_routes(doc_path)

    missing_app = sorted(app_routes - documented_routes)
    missing_admin = sorted(admin_routes - documented_routes)

    assert not missing_app, f"Missing App UI routes in NAVIGATION_ROUTES.md: {missing_app}"
    assert not missing_admin, f"Missing Admin UI routes in NAVIGATION_ROUTES.md: {missing_admin}"


def test_api_endpoints_documented():
    repo_root = Path(__file__).resolve().parents[2]
    presentation_dir = repo_root / "services" / "api" / "app" / "presentation"
    main_py = repo_root / "services" / "api" / "app" / "main.py"
    doc_path = repo_root / "ai" / "API_ENDPOINTS.md"

    endpoints = _collect_api_endpoints(presentation_dir, main_py)
    endpoint_paths = {e.path for e in endpoints}
    documented_routes = _extract_doc_routes(doc_path)

    missing = sorted(endpoint_paths - documented_routes)
    assert not missing, f"Missing API endpoints in API_ENDPOINTS.md: {missing}"
