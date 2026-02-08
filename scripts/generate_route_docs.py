#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


RE_DECORATOR = re.compile(r"@router\.(get|post|patch|delete|put)\((\"[^\"]+\"|'[^']+')")
RE_INCLUDE = re.compile(r"include_router\((\w+)\.router,\s*prefix=\"([^\"]+)\"")


@dataclass(frozen=True)
class ApiEndpoint:
    method: str
    path: str


def _is_route_segment(name: str) -> bool:
    if name.startswith((".", "_", "@")):
        return False
    if name.startswith("(") and name.endswith(")"):
        return False
    return True


def _walk_app_routes(app_root: Path) -> list[str]:
    routes: set[str] = set()
    for root, _dirs, files in os.walk(app_root):
        if "page.tsx" not in files and "page.jsx" not in files and "page.ts" not in files and "page.js" not in files:
            continue
        rel = Path(root).relative_to(app_root)
        segments = [seg for seg in rel.parts if _is_route_segment(seg)]
        if not segments:
            routes.add("/")
        else:
            routes.add("/" + "/".join(segments))
    return sorted(routes)


def _load_router_prefixes(main_py: Path) -> dict[str, str]:
    content = main_py.read_text(encoding="utf-8")
    prefixes: dict[str, str] = {}
    for match in RE_INCLUDE.finditer(content):
        router_name = match.group(1)
        prefix = match.group(2)
        prefixes[router_name] = prefix
    return prefixes


def _extract_router_endpoints(router_file: Path) -> list[ApiEndpoint]:
    endpoints: list[ApiEndpoint] = []
    content = router_file.read_text(encoding="utf-8")
    for match in RE_DECORATOR.finditer(content):
        method = match.group(1).upper()
        path_literal = match.group(2)
        path = path_literal.strip("\"'")
        endpoints.append(ApiEndpoint(method=method, path=path))
    return endpoints


def _collect_api_endpoints(presentation_dir: Path, main_py: Path) -> list[ApiEndpoint]:
    prefixes = _load_router_prefixes(main_py)
    endpoints: list[ApiEndpoint] = []
    for router_file in presentation_dir.glob("*_router.py"):
        router_name = router_file.stem
        prefix = prefixes.get(router_name)
        if not prefix:
            continue
        for endpoint in _extract_router_endpoints(router_file):
            full_path = f"{prefix}{endpoint.path}"
            endpoints.append(ApiEndpoint(method=endpoint.method, path=full_path))
    # unique
    unique = {(e.method, e.path) for e in endpoints}
    return [ApiEndpoint(m, p) for m, p in sorted(unique)]


def _render_list(title: str, items: Iterable[str]) -> str:
    lines = [f"## {title}", ""]
    for item in items:
        lines.append(f"- `{item}`")
    lines.append("")
    return "\n".join(lines)


def _render_api_table(endpoints: list[ApiEndpoint]) -> str:
    lines = [
        "## API Endpoints",
        "",
        "| Method | Endpoint |",
        "| --- | --- |",
    ]
    for endpoint in endpoints:
        lines.append(f"| {endpoint.method} | `{endpoint.path}` |")
    lines.append("")
    return "\n".join(lines)


def generate_docs(repo_root: Path) -> str:
    app_ui_root = repo_root / "services" / "app-ui" / "src" / "app"
    admin_ui_root = repo_root / "services" / "admin-ui" / "src" / "app"
    presentation_dir = repo_root / "services" / "api" / "app" / "presentation"
    main_py = repo_root / "services" / "api" / "app" / "main.py"

    app_routes = _walk_app_routes(app_ui_root)
    admin_routes = _walk_app_routes(admin_ui_root)
    api_endpoints = _collect_api_endpoints(presentation_dir, main_py)

    parts = [
        "# Generated Route Inventory",
        "",
        _render_list("App UI Routes", app_routes),
        _render_list("Admin UI Routes", admin_routes),
        _render_api_table(api_endpoints),
    ]
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate route inventory from code.")
    parser.add_argument("--out", help="Write output to file instead of stdout.")
    parser.add_argument("--repo", default=".", help="Repository root (default: .)")
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    content = generate_docs(repo_root)

    if args.out:
        Path(args.out).write_text(content, encoding="utf-8")
    else:
        print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
