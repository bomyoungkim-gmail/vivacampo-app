from datetime import date, datetime, timezone
import uuid

from sqlalchemy import text

from app.application.correlation import CorrelationService
from app.database import SessionLocal
from app.infrastructure.adapters.persistence.sqlalchemy.correlation_repository import SQLAlchemyCorrelationRepository


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


def test_correlation_service_weather_columns():
    today = date.today()
    year = today.isocalendar().year
    week = today.isocalendar().week
    now = datetime.now(timezone.utc)
    tenant_id = str(uuid.uuid4())
    identity_id = str(uuid.uuid4())
    membership_id = str(uuid.uuid4())
    farm_id = str(uuid.uuid4())
    aoi_id = str(uuid.uuid4())

    db = SessionLocal()
    try:
        _seed_minimal_data(db, tenant_id, identity_id, membership_id, farm_id, aoi_id)

        db.execute(
            text(
                """
                INSERT INTO derived_assets
                    (tenant_id, aoi_id, year, week, pipeline_version, ndvi_mean, created_at)
                VALUES
                    (:tenant_id, :aoi_id, :year, :week, 'v1', 0.55, :created_at)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "year": year,
                "week": week,
                "created_at": now,
            },
        )

        db.execute(
            text(
                """
                INSERT INTO derived_radar_assets
                    (tenant_id, aoi_id, year, week, pipeline_version, rvi_mean, created_at)
                VALUES
                    (:tenant_id, :aoi_id, :year, :week, 'v1', 0.45, :created_at)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "year": year,
                "week": week,
                "created_at": now,
            },
        )

        db.execute(
            text(
                """
                INSERT INTO derived_weather_daily
                    (tenant_id, aoi_id, date, temp_max, temp_min, precip_sum)
                VALUES
                    (:tenant_id, :aoi_id, :date, 30.0, 20.0, 12.0)
                ON CONFLICT DO NOTHING
                """
            ),
            {"tenant_id": tenant_id, "aoi_id": aoi_id, "date": today},
        )

        db.commit()

        service = CorrelationService(SQLAlchemyCorrelationRepository(db))
        data = service.fetch_correlation_data(aoi_id, tenant_id, weeks=4)

        target_key = f"{year}-W{week:02d}"
        row = next((item for item in data if item["date"] == target_key), None)

        assert row is not None
        assert row["rain_mm"] == 12.0
        assert row["temp_avg"] == 25.0
    finally:
        db.close()
