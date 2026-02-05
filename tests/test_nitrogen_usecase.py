from datetime import datetime, timezone
import uuid

from sqlalchemy import text

from app.application.nitrogen import GetNitrogenStatusUseCase
from app.database import SessionLocal


def _seed_minimal_data(db, tenant_id, identity_id, membership_id, farm_id, aoi_id):
    db.execute(
        text(
            """
            INSERT INTO identities (id, provider, subject, email, name, status)
            VALUES (:id, 'local', :subject, :email, 'Local Test', 'ACTIVE')
            ON CONFLICT DO NOTHING
            """
        ),
        {
            "id": identity_id,
            "subject": f"local-test-{identity_id}",
            "email": f"local.test+{identity_id}@vivacampo.com",
        },
    )
    db.execute(
        text(
            """
            INSERT INTO tenants (id, type, name, status, plan)
            VALUES (:id, 'COMPANY', 'Test Tenant', 'ACTIVE', 'BASIC')
            ON CONFLICT DO NOTHING
            """
        ),
        {"id": tenant_id},
    )
    db.execute(
        text(
            """
            INSERT INTO memberships (id, tenant_id, identity_id, role, status)
            VALUES (:id, :tenant_id, :identity_id, 'TENANT_ADMIN', 'ACTIVE')
            ON CONFLICT DO NOTHING
            """
        ),
        {"id": membership_id, "tenant_id": tenant_id, "identity_id": identity_id},
    )
    db.execute(
        text(
            """
            INSERT INTO farms (id, tenant_id, name, timezone)
            VALUES (:id, :tenant_id, 'Test Farm', 'America/Sao_Paulo')
            ON CONFLICT DO NOTHING
            """
        ),
        {"id": farm_id, "tenant_id": tenant_id},
    )
    db.execute(
        text(
            """
            INSERT INTO aois (id, tenant_id, farm_id, name, use_type, status, geom, area_ha)
            VALUES (
                :id,
                :tenant_id,
                :farm_id,
                'Test AOI',
                'CROP',
                'ACTIVE',
                ST_GeomFromText('MULTIPOLYGON(((-47.1 -23.5, -47.1 -23.49, -47.09 -23.49, -47.09 -23.5, -47.1 -23.5)))', 4326),
                50.0
            )
            ON CONFLICT DO NOTHING
            """
        ),
        {"id": aoi_id, "tenant_id": tenant_id, "farm_id": farm_id},
    )


def test_nitrogen_status_deficient():
    tenant_id = str(uuid.uuid4())
    identity_id = str(uuid.uuid4())
    membership_id = str(uuid.uuid4())
    farm_id = str(uuid.uuid4())
    aoi_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    db = SessionLocal()
    try:
        _seed_minimal_data(db, tenant_id, identity_id, membership_id, farm_id, aoi_id)

        db.execute(
            text(
                """
                INSERT INTO derived_assets
                    (tenant_id, aoi_id, year, week, pipeline_version, ndvi_mean, ndre_mean, reci_mean, created_at)
                VALUES
                    (:tenant_id, :aoi_id, 2026, 6, 'v1', 0.78, 0.40, 1.20, :created_at)
                ON CONFLICT DO NOTHING
                """
            ),
            {"tenant_id": tenant_id, "aoi_id": aoi_id, "created_at": now},
        )
        db.commit()

        use_case = GetNitrogenStatusUseCase(db)
        result = use_case.execute(tenant_id, aoi_id, "http://localhost:8000")

        assert result["status"] == "DEFICIENT"
        assert result["confidence"] == 0.9
        assert result["zone_map_url"].endswith("/v1/tiles/aois/" + aoi_id + "/{z}/{x}/{y}.png?index=srre")
    finally:
        db.close()
