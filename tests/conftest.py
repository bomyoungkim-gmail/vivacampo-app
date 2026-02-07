import os
import sys
from urllib.parse import urlparse, urlunparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import uuid

import pytest
from jose import jwt


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "infra" / "docker" / "env" / ".env.local"

worker_path = ROOT / "services" / "worker"
if str(worker_path) not in sys.path:
    sys.path.insert(0, str(worker_path))


def _load_env_file(path: Path) -> dict[str, str]:
    env = {}
    if not path.exists():
        return env
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        env[key.strip()] = value
    return env


_ENV = _load_env_file(ENV_PATH)


def _ensure_env() -> None:
    for key, value in _ENV.items():
        os.environ.setdefault(key, value)


def _apply_db_host_overrides() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return

    host_override = os.environ.get("DATABASE_HOST_OVERRIDE")
    port_override = os.environ.get("DATABASE_PORT_OVERRIDE")

    if not host_override and os.name == "nt":
        parsed = urlparse(database_url)
        if parsed.hostname == "db":
            host_override = "localhost"

    if not (host_override or port_override):
        return

    parsed = urlparse(database_url)
    host = host_override or parsed.hostname or ""
    port = port_override or parsed.port
    userinfo = ""
    if parsed.username:
        userinfo = parsed.username
        if parsed.password:
            userinfo = f"{userinfo}:{parsed.password}"

    netloc = host
    if port:
        netloc = f"{netloc}:{port}"
    if userinfo:
        netloc = f"{userinfo}@{netloc}"

    os.environ["DATABASE_URL"] = urlunparse(parsed._replace(netloc=netloc))


_ensure_env()
_apply_db_host_overrides()


api_path = ROOT / "services" / "api"
if str(api_path) not in sys.path:
    sys.path.insert(0, str(api_path))


@pytest.fixture(scope="session", autouse=True)
def ensure_db_schema() -> None:
    _ensure_env()
    from sqlalchemy import text
    from app import database
    from app.infrastructure import models  # noqa: F401

    database.Base.metadata.create_all(bind=database.engine)
    with database.engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tenant_settings (
                tenant_id uuid PRIMARY KEY,
                max_cloud_cover int NOT NULL DEFAULT 60,
                min_valid_pixel_ratio double precision NOT NULL DEFAULT 0.15,
                alert_thresholds jsonb NOT NULL DEFAULT '{}'::jsonb,
                notifications jsonb NOT NULL DEFAULT '{}'::jsonb,
                updated_at timestamptz NOT NULL DEFAULT now(),
                updated_by_membership_id uuid NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id uuid NULL,
                actor_type text NOT NULL,
                actor_id uuid NULL,
                action text NOT NULL,
                resource_type text NOT NULL,
                resource_id uuid NULL,
                diff_json jsonb NULL,
                metadata_json jsonb NULL,
                created_at timestamptz NOT NULL DEFAULT now()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_assistant_threads (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id uuid NOT NULL,
                aoi_id uuid NULL,
                signal_id uuid NULL,
                created_by_membership_id uuid NOT NULL,
                provider text NOT NULL,
                model text NOT NULL,
                status text NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_assistant_checkpoints (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id uuid NOT NULL,
                thread_id uuid NOT NULL,
                step int NOT NULL,
                state_json text NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_assistant_approvals (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id uuid NOT NULL,
                thread_id uuid NOT NULL,
                tool_name text NOT NULL,
                tool_payload text NOT NULL,
                decision text NOT NULL DEFAULT 'PENDING',
                created_at timestamptz NOT NULL DEFAULT now()
            )
        """))


def _build_oidc_token() -> str:
    payload = {
        "sub": "local-test-user",
        "email": "test.user@example.com",
        "name": "Test User",
    }
    secret = os.environ["JWT_SECRET"]
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture(scope="session")
def oidc_id_token() -> str:
    return _build_oidc_token()


def _create_local_session_token() -> str:
    from app.auth.utils import create_session_token
    from app.database import SessionLocal
    from app.infrastructure.models import Identity, Membership, Tenant

    with SessionLocal() as db:
        tenant = Tenant(
            type="PERSONAL",
            name=f"Test Tenant {uuid.uuid4()}",
            status="ACTIVE",
            plan="BASIC",
            quotas={},
        )
        db.add(tenant)
        db.flush()

        identity = Identity(
            provider="local",
            subject=f"test-user-{uuid.uuid4()}",
            email=f"test-user-{uuid.uuid4()}@example.com",
            name="Test User",
            status="ACTIVE",
        )
        db.add(identity)
        db.flush()

        membership = Membership(
            tenant_id=tenant.id,
            identity_id=identity.id,
            role="TENANT_ADMIN",
            status="ACTIVE",
        )
        db.add(membership)
        db.commit()

        return create_session_token(
            tenant_id=tenant.id,
            membership_id=membership.id,
            identity_id=identity.id,
            role="TENANT_ADMIN",
        )


@pytest.fixture
async def session_token() -> str:
    return _create_local_session_token()


@pytest.fixture
async def auth_headers(session_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {session_token}",
        "Content-Type": "application/json",
    }


def _ensure_system_admin(identity_id: uuid.UUID) -> None:
    from app.database import SessionLocal
    from app.infrastructure.models import Identity, SystemAdmin

    session = SessionLocal()
    try:
        identity = session.query(Identity).filter(Identity.id == identity_id).first()
        if not identity:
            identity = Identity(
                id=identity_id,
                provider="local",
                subject="system-admin",
                email="system-admin@example.com",
                name="System Admin",
                status="ACTIVE",
            )
            session.add(identity)

        system_admin = session.query(SystemAdmin).filter(
            SystemAdmin.identity_id == identity_id
        ).first()
        if not system_admin:
            system_admin = SystemAdmin(
                identity_id=identity_id,
                role="SYSTEM_ADMIN",
                status="ACTIVE",
            )
            session.add(system_admin)

        session.commit()
    finally:
        session.close()


@pytest.fixture(scope="session")
def system_admin_headers() -> dict[str, str]:
    _ensure_env()
    identity_id = uuid.UUID("00000000-0000-0000-0000-000000000099")
    _ensure_system_admin(identity_id)

    payload = {
        "sub": str(identity_id),
        "iss": os.environ["SYSTEM_ADMIN_ISSUER"],
        "aud": os.environ["SYSTEM_ADMIN_AUDIENCE"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def pytest_collection_modifyitems(config, items):
    for item in items:
        nodeid = item.nodeid.replace("\\", "/")
        if "/tests/unit/" in nodeid:
            item.add_marker(pytest.mark.unit)
        elif "/tests/security/" in nodeid:
            item.add_marker(pytest.mark.security)
            item.add_marker(pytest.mark.integration)
        elif "/tests/contract/" in nodeid:
            item.add_marker(pytest.mark.contract)
        elif nodeid.endswith("tests/test_e2e.py") or nodeid.endswith("tests/test_e2e.py::"):
            item.add_marker(pytest.mark.e2e)
        elif any(
            name in nodeid
            for name in (
                "tests/test_integration_complete.py",
                "tests/test_worker_jobs.py",
                "tests/test_worker_aws_integration.py",
                "tests/test_api_aws_integration.py",
                "tests/test_integrations_p2.py",
                "tests/test_rbac.py",
            )
        ):
            item.add_marker(pytest.mark.integration)
