import uuid
from uuid import UUID

import httpx
import pytest

from app.auth.utils import create_session_token, decode_session_token
from app.database import SessionLocal
from app.infrastructure.models import Identity, Membership, Tenant

API_BASE = "http://localhost:8000"


def _decode_tenant_id_from_headers(headers: dict[str, str]) -> UUID:
    token = headers["Authorization"].split(" ", 1)[1]
    payload = decode_session_token(token)
    return UUID(payload["tenant_id"])


@pytest.fixture
async def viewer_headers(auth_headers: dict[str, str]) -> dict[str, str]:
    tenant_id = _decode_tenant_id_from_headers(auth_headers)

    with SessionLocal() as db:
        viewer_identity = Identity(
            provider="local",
            subject=f"rbac-viewer-{uuid.uuid4()}",
            email=f"rbac-viewer-{uuid.uuid4()}@example.com",
            name="RBAC Viewer",
            status="ACTIVE",
        )
        db.add(viewer_identity)
        db.flush()

        viewer_membership = Membership(
            tenant_id=tenant_id,
            identity_id=viewer_identity.id,
            role="VIEWER",
            status="ACTIVE",
        )
        db.add(viewer_membership)
        db.commit()

        viewer_identity_id = viewer_identity.id
        viewer_membership_id = viewer_membership.id

    viewer_token = create_session_token(
        tenant_id=tenant_id,
        membership_id=viewer_membership_id,
        identity_id=viewer_identity_id,
        role="VIEWER",
    )

    return {
        "Authorization": f"Bearer {viewer_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def other_tenant_EDITOR_headers() -> dict[str, str]:
    with SessionLocal() as db:
        other_tenant = Tenant(
            type="COMPANY",
            name=f"RBAC Tenant {uuid.uuid4()}",
            status="ACTIVE",
            plan="ENTERPRISE",
            quotas={},
        )
        db.add(other_tenant)
        db.flush()

        identity = Identity(
            provider="local",
            subject=f"rbac-cross-{uuid.uuid4()}",
            email=f"rbac-cross-{uuid.uuid4()}@example.com",
            name="Cross Tenant EDITOR",
            status="ACTIVE",
        )
        db.add(identity)
        db.flush()

        membership = Membership(
            tenant_id=other_tenant.id,
            identity_id=identity.id,
            role="EDITOR",
            status="ACTIVE",
        )
        db.add(membership)
        db.commit()

        tenant_id = other_tenant.id
        membership_id = membership.id
        identity_id = identity.id

    token = create_session_token(
        tenant_id=tenant_id,
        membership_id=membership_id,
        identity_id=identity_id,
        role="EDITOR",
    )

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
async def tenant_a_aoi(auth_headers: dict[str, str]) -> dict[str, str]:
    async with httpx.AsyncClient() as client:
        farm_payload = {
            "name": f"RBAC Farm {uuid.uuid4()}",
            "timezone": "America/Sao_Paulo",
        }
        farm_response = await client.post(
            f"{API_BASE}/v1/app/farms",
            headers=auth_headers,
            json=farm_payload,
        )
        farm_response.raise_for_status()
        farm_id = farm_response.json()["id"]

        aoi_payload = {
            "farm_id": farm_id,
            "name": f"RBAC AOI {uuid.uuid4()}",
            "use_type": "PASTURE",
            "geometry": "MULTIPOLYGON(((-47.0 -23.0, -47.0 -23.001, -47.001 -23.001, -47.001 -23.0, -47.0 -23.0)))",
        }
        aoi_response = await client.post(
            f"{API_BASE}/v1/app/aois",
            headers=auth_headers,
            json=aoi_payload,
        )
        aoi_response.raise_for_status()

    return {"farm_id": farm_id, "aoi_id": aoi_response.json()["id"]}


class TestRBAC:
    async def test_viewer_cannot_create_farm(self, viewer_headers: dict[str, str]) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/v1/app/farms",
                headers=viewer_headers,
                json={"name": "RBAC Unauthorized Farm", "timezone": "America/Sao_Paulo"},
            )

        assert response.status_code == 403, response.text
        assert response.json()["error"]["message"].startswith("Insufficient permissions")

    async def test_cross_tenant_EDITOR_cannot_backfill_other_aoi(
        self,
        other_tenant_EDITOR_headers: dict[str, str],
        tenant_a_aoi: dict[str, str],
    ) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/v1/app/aois/{tenant_a_aoi['aoi_id']}/backfill",
                headers=other_tenant_EDITOR_headers,
                json={
                    "from_date": "2024-01-01",
                    "to_date": "2024-01-08",
                    "cadence": "weekly",
                },
            )

        assert response.status_code == 404, response.text
        assert response.json()["error"]["message"] == "AOI not found"
