import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.auth.utils import create_session_token
from app.database import SessionLocal
from app.infrastructure.models import Identity, Membership, Tenant, Farm
from app.main import app


def _create_tenant(db, name: str) -> Tenant:
    tenant = Tenant(type="COMPANY", name=name, status="ACTIVE", plan="ENTERPRISE", quotas={})
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def _create_membership(db, tenant_id: uuid.UUID, role: str = "EDITOR") -> tuple[Identity, Membership]:
    identity = Identity(
        provider="local",
        subject=f"security-{uuid.uuid4()}",
        email=f"security-{uuid.uuid4()}@example.com",
        name="Security Test",
        status="ACTIVE",
    )
    db.add(identity)
    db.commit()
    db.refresh(identity)

    membership = Membership(
        tenant_id=tenant_id,
        identity_id=identity.id,
        role=role,
        status="ACTIVE",
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return identity, membership


def _auth_headers(tenant_id: uuid.UUID, membership_id: uuid.UUID, identity_id: uuid.UUID, role: str) -> dict[str, str]:
    token = create_session_token(
        tenant_id=tenant_id,
        membership_id=membership_id,
        identity_id=identity_id,
        role=role,
    )
    return {"Authorization": f"Bearer {token}"}


def _auth_headers_with_mismatch(
    tenant_id: uuid.UUID, membership_id: uuid.UUID, identity_id: uuid.UUID, role: str
) -> dict[str, str]:
    # Intentionally pass a different tenant_id into the token.
    wrong_tenant_id = uuid.uuid4()
    token = create_session_token(
        tenant_id=wrong_tenant_id,
        membership_id=membership_id,
        identity_id=identity_id,
        role=role,
    )
    return {"Authorization": f"Bearer {token}"}


def _create_farm(db, tenant_id: uuid.UUID, name: str) -> Farm:
    farm = Farm(tenant_id=tenant_id, name=name, timezone="America/Sao_Paulo")
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


def _create_aoi(db, tenant_id: uuid.UUID, farm_id: uuid.UUID, name: str) -> uuid.UUID:
    sql = text(
        """
        INSERT INTO aois (tenant_id, farm_id, name, use_type, geom, area_ha, status)
        VALUES (:tenant_id, :farm_id, :name, :use_type, ST_GeomFromText(:geom, 4326), :area_ha, :status)
        RETURNING id
        """
    )
    row = db.execute(
        sql,
        {
            "tenant_id": str(tenant_id),
            "farm_id": str(farm_id),
            "name": name,
            "use_type": "PASTURE",
            "geom": "MULTIPOLYGON(((0 0,0 1,1 1,1 0,0 0)))",
            "area_ha": 1.0,
            "status": "ACTIVE",
        },
    ).fetchone()
    db.commit()
    return row.id


@pytest.mark.integration
def test_list_farms_isolated_by_tenant():
    client = TestClient(app)
    db = SessionLocal()
    try:
        tenant_a = _create_tenant(db, "Tenant A")
        tenant_b = _create_tenant(db, "Tenant B")

        identity_a, membership_a = _create_membership(db, tenant_a.id, role="EDITOR")
        identity_b, membership_b = _create_membership(db, tenant_b.id, role="EDITOR")

        farm_a = _create_farm(db, tenant_a.id, "Farm A")
        _create_farm(db, tenant_b.id, "Farm B")

        headers_a = _auth_headers(tenant_a.id, membership_a.id, identity_a.id, membership_a.role)
        headers_b = _auth_headers(tenant_b.id, membership_b.id, identity_b.id, membership_b.role)

        resp_a = client.get("/v1/app/farms", headers=headers_a)
        assert resp_a.status_code == 200
        ids_a = {item["id"] for item in resp_a.json()}
        assert str(farm_a.id) in ids_a
        assert len(ids_a) == 1

        resp_b = client.get("/v1/app/farms", headers=headers_b)
        assert resp_b.status_code == 200
        ids_b = {item["id"] for item in resp_b.json()}
        assert str(farm_a.id) not in ids_b
        assert len(ids_b) == 1
    finally:
        db.close()


@pytest.mark.integration
def test_backfill_rejects_cross_tenant_aoi():
    client = TestClient(app)
    db = SessionLocal()
    try:
        tenant_a = _create_tenant(db, "Tenant C")
        tenant_b = _create_tenant(db, "Tenant D")

        identity_a, membership_a = _create_membership(db, tenant_a.id, role="EDITOR")

        farm_b = _create_farm(db, tenant_b.id, "Farm D")
        aoi_b = _create_aoi(db, tenant_b.id, farm_b.id, "AOI D")

        headers_a = _auth_headers(tenant_a.id, membership_a.id, identity_a.id, membership_a.role)
        payload = {
            "from_date": (datetime.now(UTC) - timedelta(days=14)).date().isoformat(),
            "to_date": datetime.now(UTC).date().isoformat(),
            "cadence": "weekly",
        }

        resp = client.post(f"/v1/app/aois/{aoi_b}/backfill", json=payload, headers=headers_a)
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["message"] == "AOI not found"
    finally:
        db.close()


@pytest.mark.integration
def test_membership_token_mismatch_rejected():
    client = TestClient(app)
    db = SessionLocal()
    try:
        tenant = _create_tenant(db, "Tenant E")
        identity, membership = _create_membership(db, tenant.id, role="EDITOR")
        farm = _create_farm(db, tenant.id, "Farm E")
        _create_aoi(db, tenant.id, farm.id, "AOI E")

        headers = _auth_headers_with_mismatch(tenant.id, membership.id, identity.id, membership.role)
        resp = client.get("/v1/app/farms", headers=headers)
        assert resp.status_code == 401
        body = resp.json()
        assert body["error"]["message"] == "Membership does not match token claims"
    finally:
        db.close()


@pytest.mark.integration
def test_workspace_switch_rejects_other_identity_membership():
    client = TestClient(app)
    db = SessionLocal()
    try:
        tenant_a = _create_tenant(db, "Tenant F")
        tenant_b = _create_tenant(db, "Tenant G")

        identity_a, membership_a = _create_membership(db, tenant_a.id, role="EDITOR")
        identity_b, membership_b = _create_membership(db, tenant_b.id, role="EDITOR")

        headers_a = _auth_headers(tenant_a.id, membership_a.id, identity_a.id, membership_a.role)
        resp = client.post(
            "/v1/auth/workspaces/switch",
            json={"tenant_id": str(tenant_b.id)},
            headers=headers_a,
        )

        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["message"] == "Membership not found or inactive"
    finally:
        db.close()
