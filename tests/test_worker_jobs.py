import json
import sys
import types
import uuid
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[1]
WORKER_PATH = ROOT / "services" / "worker"
if str(WORKER_PATH) not in sys.path:
    sys.path.insert(0, str(WORKER_PATH))


try:
    import rasterio  # noqa: F401
except Exception:
    stub = types.ModuleType("rasterio")

    def _stub_open(*args, **kwargs):  # noqa: ANN001
        raise RuntimeError("rasterio is not available in this test environment")

    stub.open = _stub_open
    sys.modules["rasterio"] = stub


def _ensure_worker_tables(db) -> None:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS observations_weekly (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
            year int NOT NULL,
            week int NOT NULL,
            pipeline_version text NOT NULL,
            status text NOT NULL,
            valid_pixel_ratio double precision NOT NULL,
            ndvi_mean double precision NULL,
            ndvi_p10 double precision NULL,
            ndvi_p50 double precision NULL,
            ndvi_p90 double precision NULL,
            ndvi_std double precision NULL,
            baseline double precision NULL,
            anomaly double precision NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (tenant_id, aoi_id, year, week, pipeline_version)
        )
    """))

    db.execute(text("""
        CREATE TABLE IF NOT EXISTS alerts (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
            year int NULL,
            week int NULL,
            alert_type text NOT NULL,
            status text NOT NULL DEFAULT 'OPEN',
            severity text NOT NULL,
            confidence text NOT NULL,
            evidence_json jsonb NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
    """))

    db.execute(text("""
        CREATE TABLE IF NOT EXISTS seasons (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
            season_year int NOT NULL,
            start_date date NOT NULL,
            end_date date NULL,
            crop_type text NULL,
            planted_date date NULL,
            expected_harvest_date date NULL,
            status text NOT NULL DEFAULT 'ACTIVE',
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """))

    db.execute(text("""
        CREATE TABLE IF NOT EXISTS yield_forecasts (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            aoi_id uuid NOT NULL REFERENCES aois(id) ON DELETE CASCADE,
            season_year int NOT NULL DEFAULT 2024,
            model_version text NOT NULL DEFAULT 'forecast-v1',
            pipeline_version text NOT NULL DEFAULT 'v1',
            index_p10 double precision NOT NULL DEFAULT 0,
            index_p50 double precision NOT NULL DEFAULT 0,
            index_p90 double precision NOT NULL DEFAULT 0,
            season_id uuid NULL REFERENCES seasons(id) ON DELETE SET NULL,
            year int NOT NULL,
            week int NOT NULL,
            method text NOT NULL,
            estimated_yield_kg_ha double precision NOT NULL,
            actual_yield_kg_ha double precision NULL,
            confidence text NOT NULL,
            model_version text NOT NULL,
            evidence_json jsonb NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (tenant_id, aoi_id, season_id, year, week)
        )
    """))

    db.execute(text("""
        ALTER TABLE alerts
            ADD COLUMN IF NOT EXISTS year int,
            ADD COLUMN IF NOT EXISTS week int
    """))
    db.execute(text("""
        ALTER TABLE seasons
            ADD COLUMN IF NOT EXISTS crop_type text,
            ADD COLUMN IF NOT EXISTS planted_date date,
            ADD COLUMN IF NOT EXISTS expected_harvest_date date,
            ADD COLUMN IF NOT EXISTS status text,
            ADD COLUMN IF NOT EXISTS season_year int,
            ADD COLUMN IF NOT EXISTS start_date date,
            ADD COLUMN IF NOT EXISTS end_date date
    """))
    db.execute(text("""
        ALTER TABLE yield_forecasts
            ADD COLUMN IF NOT EXISTS season_id uuid,
            ADD COLUMN IF NOT EXISTS year int,
            ADD COLUMN IF NOT EXISTS week int,
            ADD COLUMN IF NOT EXISTS method text,
            ADD COLUMN IF NOT EXISTS estimated_yield_kg_ha double precision,
            ADD COLUMN IF NOT EXISTS actual_yield_kg_ha double precision,
            ADD COLUMN IF NOT EXISTS confidence text,
            ADD COLUMN IF NOT EXISTS model_version text,
            ADD COLUMN IF NOT EXISTS evidence_json jsonb,
            ADD COLUMN IF NOT EXISTS updated_at timestamptz
    """))
    db.execute(text("""
        ALTER TABLE yield_forecasts
            ALTER COLUMN season_year SET DEFAULT 2024,
            ALTER COLUMN model_version SET DEFAULT 'forecast-v1',
            ALTER COLUMN pipeline_version SET DEFAULT 'v1',
            ALTER COLUMN index_p10 SET DEFAULT 0,
            ALTER COLUMN index_p50 SET DEFAULT 0,
            ALTER COLUMN index_p90 SET DEFAULT 0,
            ALTER COLUMN confidence SET DEFAULT 'LOW'
    """))
    db.execute(text("""
        ALTER TABLE seasons
            ALTER COLUMN status SET DEFAULT 'ACTIVE'
    """))
    db.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS yield_forecasts_season_week_idx
        ON yield_forecasts (tenant_id, aoi_id, season_id, year, week)
    """))

    db.commit()


@pytest.fixture
def db_session():
    from app.database import SessionLocal

    session = SessionLocal()
    _ensure_worker_tables(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def tenant_farm_aoi(db_session):
    tenant_id = uuid.uuid4()
    farm_id = uuid.uuid4()
    aoi_id = uuid.uuid4()

    db_session.execute(
        text("""
            INSERT INTO tenants (id, type, name, status, plan, quotas)
            VALUES (:id, 'COMPANY', 'Test Tenant', 'ACTIVE', 'BASIC', '{}'::jsonb)
        """),
        {"id": str(tenant_id)},
    )
    db_session.execute(
        text("""
            INSERT INTO farms (id, tenant_id, name, timezone)
            VALUES (:id, :tenant_id, 'Test Farm', 'America/Sao_Paulo')
        """),
        {"id": str(farm_id), "tenant_id": str(tenant_id)},
    )
    db_session.execute(
        text("""
            INSERT INTO aois (id, tenant_id, farm_id, name, use_type, status, geom, area_ha)
            VALUES (
                :id, :tenant_id, :farm_id, 'Test AOI', 'CROP', 'ACTIVE',
                ST_GeomFromText(:geom, 4326), :area_ha
            )
        """),
        {
            "id": str(aoi_id),
            "tenant_id": str(tenant_id),
            "farm_id": str(farm_id),
            "geom": "MULTIPOLYGON(((-47.0 -23.0, -47.0 -23.1, -47.1 -23.1, -47.1 -23.0, -47.0 -23.0)))",
            "area_ha": 10.0,
        },
    )
    db_session.commit()

    try:
        yield {
            "tenant_id": str(tenant_id),
            "farm_id": str(farm_id),
            "aoi_id": str(aoi_id),
        }
    finally:
        db_session.execute(
            text("DELETE FROM tenants WHERE id = :tenant_id"),
            {"tenant_id": str(tenant_id)},
        )
        db_session.commit()


def _insert_job(db, tenant_id: str, aoi_id: str, job_type: str, payload: dict) -> str:
    job_id = str(uuid.uuid4())
    job_key = f"test-{job_type}-{job_id}"
    db.execute(
        text("""
            INSERT INTO jobs (id, tenant_id, aoi_id, job_type, job_key, status, payload_json)
            VALUES (:id, :tenant_id, :aoi_id, :job_type, :job_key, 'PENDING', :payload)
        """),
        {
            "id": job_id,
            "tenant_id": tenant_id,
            "aoi_id": aoi_id,
            "job_type": job_type,
            "job_key": job_key,
            "payload": json.dumps(payload),
        },
    )
    db.commit()
    return job_id


@pytest.mark.asyncio
async def test_backfill_creates_child_jobs_and_marks_done(db_session, tenant_farm_aoi, monkeypatch):
    from worker.jobs import backfill as backfill_job
    from worker.config import settings

    created_messages = []

    class DummySQS:
        def send_message(self, message_body, queue_url=None):  # noqa: ANN001
            created_messages.append(message_body)

    monkeypatch.setattr("worker.shared.aws_clients.SQSClient", lambda: DummySQS())
    monkeypatch.setattr(settings, "signals_enabled", True)

    db_session.execute(
        text("""
            INSERT INTO seasons (
                tenant_id, aoi_id, season_year, start_date, end_date,
                crop_type, planted_date, expected_harvest_date, status
            )
            VALUES (
                :tenant_id, :aoi_id, :season_year, :start_date, :end_date,
                'CORN', :planted, :harvest, 'ACTIVE'
            )
        """),
        {
            "tenant_id": tenant_farm_aoi["tenant_id"],
            "aoi_id": tenant_farm_aoi["aoi_id"],
            "season_year": 2024,
            "start_date": date(2023, 10, 1),
            "end_date": None,
            "planted": date(2023, 10, 1),
            "harvest": date(2024, 3, 15),
        },
    )
    db_session.commit()

    payload = {
        "tenant_id": tenant_farm_aoi["tenant_id"],
        "aoi_id": tenant_farm_aoi["aoi_id"],
        "from_date": "2024-01-01",
        "to_date": "2024-01-08",
    }

    job_id = _insert_job(db_session, tenant_farm_aoi["tenant_id"], tenant_farm_aoi["aoi_id"], "BACKFILL", payload)

    result = await backfill_job.handle_backfill(
        {
            "id": job_id,
            "tenant_id": tenant_farm_aoi["tenant_id"],
            "aoi_id": tenant_farm_aoi["aoi_id"],
            "payload": payload,
        },
        db_session,
    )

    assert result["weeks_processed"] == 2
    assert result["total_jobs"] == 8
    assert len(created_messages) == 8

    status = db_session.execute(
        text("SELECT status FROM jobs WHERE id = :job_id"),
        {"job_id": job_id},
    ).scalar_one()
    assert status == "DONE"

    created = db_session.execute(
        text("""
            SELECT job_type, COUNT(*)
            FROM jobs
            WHERE tenant_id = :tenant_id AND job_type != 'BACKFILL'
            GROUP BY job_type
        """),
        {"tenant_id": tenant_farm_aoi["tenant_id"]},
    ).fetchall()
    created_map = {row[0]: row[1] for row in created}
    assert created_map.get("PROCESS_WEEK") == 2
    assert created_map.get("ALERTS_WEEK") == 2
    assert created_map.get("SIGNALS_WEEK") == 2
    assert created_map.get("FORECAST_WEEK") == 2


def test_process_week_handler_updates_status_and_observation(db_session, tenant_farm_aoi, monkeypatch):
    from worker.jobs import process_week as process_week_job

    payload = {
        "tenant_id": tenant_farm_aoi["tenant_id"],
        "aoi_id": tenant_farm_aoi["aoi_id"],
        "year": 2024,
        "week": 1,
    }
    job_id = _insert_job(db_session, tenant_farm_aoi["tenant_id"], tenant_farm_aoi["aoi_id"], "PROCESS_WEEK", payload)

    async def fake_process_week_async(job_id_arg, payload_arg, db):  # noqa: ANN001
        db.execute(
            text("""
                INSERT INTO observations_weekly
                (tenant_id, aoi_id, year, week, pipeline_version, status, valid_pixel_ratio,
                 ndvi_mean, ndvi_p10, ndvi_p50, ndvi_p90, ndvi_std, baseline, anomaly)
                VALUES
                (:tenant_id, :aoi_id, :year, :week, 'v1', 'OK', 0.5,
                 0.6, 0.5, 0.6, 0.7, 0.1, 0.55, 0.05)
            """),
            {
                "tenant_id": payload_arg["tenant_id"],
                "aoi_id": payload_arg["aoi_id"],
                "year": payload_arg["year"],
                "week": payload_arg["week"],
            },
        )
        db.commit()
        process_week_job.update_job_status(job_id_arg, "DONE", db)

    monkeypatch.setattr(process_week_job, "process_week_async", fake_process_week_async)

    process_week_job.process_week_handler(job_id, payload, db_session)

    status = db_session.execute(
        text("SELECT status FROM jobs WHERE id = :job_id"),
        {"job_id": job_id},
    ).scalar_one()
    assert status == "DONE"

    obs_count = db_session.execute(
        text("""
            SELECT COUNT(*)
            FROM observations_weekly
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id AND year = 2024 AND week = 1
        """),
        {"tenant_id": tenant_farm_aoi["tenant_id"], "aoi_id": tenant_farm_aoi["aoi_id"]},
    ).scalar_one()
    assert obs_count == 1


@pytest.mark.asyncio
async def test_alerts_week_creates_alerts(db_session, tenant_farm_aoi):
    from worker.jobs import alerts_week as alerts_job

    db_session.execute(
        text("""
            INSERT INTO observations_weekly
            (tenant_id, aoi_id, year, week, pipeline_version, status, valid_pixel_ratio,
             ndvi_mean, ndvi_p10, ndvi_p50, ndvi_p90, ndvi_std, baseline, anomaly)
            VALUES
            (:tenant_id, :aoi_id, 2024, 2, 'v1', 'OK', 0.1,
             0.25, 0.2, 0.25, 0.3, 0.05, 0.3, -0.1)
        """),
        {"tenant_id": tenant_farm_aoi["tenant_id"], "aoi_id": tenant_farm_aoi["aoi_id"]},
    )
    db_session.execute(
        text("""
            INSERT INTO observations_weekly
            (tenant_id, aoi_id, year, week, pipeline_version, status, valid_pixel_ratio,
             ndvi_mean, ndvi_p10, ndvi_p50, ndvi_p90, ndvi_std, baseline, anomaly)
            VALUES
            (:tenant_id, :aoi_id, 2024, 1, 'v1', 'OK', 0.6,
             0.55, 0.5, 0.55, 0.6, 0.05, 0.55, 0.01)
        """),
        {"tenant_id": tenant_farm_aoi["tenant_id"], "aoi_id": tenant_farm_aoi["aoi_id"]},
    )
    db_session.commit()

    job_id = _insert_job(
        db_session,
        tenant_farm_aoi["tenant_id"],
        tenant_farm_aoi["aoi_id"],
        "ALERTS_WEEK",
        {"tenant_id": tenant_farm_aoi["tenant_id"], "aoi_id": tenant_farm_aoi["aoi_id"], "year": 2024, "week": 2},
    )

    result = await alerts_job.handle_alerts_week(
        {
            "id": job_id,
            "tenant_id": tenant_farm_aoi["tenant_id"],
            "aoi_id": tenant_farm_aoi["aoi_id"],
            "payload": {"year": 2024, "week": 2},
        },
        db_session,
    )

    assert result["alerts_created"] >= 2

    alert_types = db_session.execute(
        text("""
            SELECT alert_type
            FROM alerts
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id AND year = 2024 AND week = 2
        """),
        {"tenant_id": tenant_farm_aoi["tenant_id"], "aoi_id": tenant_farm_aoi["aoi_id"]},
    ).fetchall()
    alert_type_set = {row[0] for row in alert_types}
    assert "NO_DATA" in alert_type_set
    assert "LOW_NDVI" in alert_type_set


def test_signals_week_creates_signal(db_session, tenant_farm_aoi, monkeypatch):
    from worker.jobs import signals_week as signals_job
    from worker.config import settings

    monkeypatch.setattr(settings, "signals_min_history_weeks", 2)
    monkeypatch.setattr(settings, "signals_score_threshold", 0.0)
    monkeypatch.setattr(settings, "signals_change_detection", "Simple")

    monkeypatch.setattr(signals_job, "extract_features", lambda observations: {"trend": 0.1})
    monkeypatch.setattr(signals_job, "calculate_rule_score", lambda features, use_type: 0.8)
    monkeypatch.setattr(signals_job, "calculate_ml_score", lambda features: 0.8)
    monkeypatch.setattr(signals_job, "calculate_change_score", lambda change: 0.8)
    monkeypatch.setattr(signals_job, "calculate_final_score", lambda r, c, m: 0.9)
    monkeypatch.setattr(signals_job, "determine_severity", lambda score: "HIGH")
    monkeypatch.setattr(signals_job, "determine_confidence", lambda score, vpr, count: "HIGH")
    monkeypatch.setattr(signals_job, "determine_signal_type", lambda use_type, features, change: "VIGOR_DROP")
    monkeypatch.setattr(signals_job, "get_recommended_actions", lambda signal_type: ["IRRIGATE"])
    monkeypatch.setattr(signals_job, "detect_change_simple", lambda observations: {"change": 0.2})

    db_session.execute(
        text("""
            INSERT INTO observations_weekly
            (tenant_id, aoi_id, year, week, pipeline_version, status, valid_pixel_ratio,
             ndvi_mean, ndvi_p10, ndvi_p50, ndvi_p90, ndvi_std, baseline, anomaly)
            VALUES
            (:tenant_id, :aoi_id, 2024, 1, 'v1', 'OK', 0.8,
             0.6, 0.5, 0.6, 0.7, 0.05, 0.6, 0.01),
            (:tenant_id, :aoi_id, 2024, 2, 'v1', 'OK', 0.8,
             0.55, 0.45, 0.55, 0.65, 0.05, 0.58, -0.02)
        """),
        {"tenant_id": tenant_farm_aoi["tenant_id"], "aoi_id": tenant_farm_aoi["aoi_id"]},
    )
    db_session.commit()

    job_id = _insert_job(
        db_session,
        tenant_farm_aoi["tenant_id"],
        tenant_farm_aoi["aoi_id"],
        "SIGNALS_WEEK",
        {"tenant_id": tenant_farm_aoi["tenant_id"], "aoi_id": tenant_farm_aoi["aoi_id"], "year": 2024, "week": 2},
    )

    signals_job.signals_week_handler(
        job_id,
        {"tenant_id": tenant_farm_aoi["tenant_id"], "aoi_id": tenant_farm_aoi["aoi_id"], "year": 2024, "week": 2},
        db_session,
    )

    status = db_session.execute(
        text("SELECT status FROM jobs WHERE id = :job_id"),
        {"job_id": job_id},
    ).scalar_one()
    assert status == "DONE"

    signal_count = db_session.execute(
        text("""
            SELECT COUNT(*)
            FROM opportunity_signals
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id AND year = 2024 AND week = 2
        """),
        {"tenant_id": tenant_farm_aoi["tenant_id"], "aoi_id": tenant_farm_aoi["aoi_id"]},
    ).scalar_one()
    assert signal_count == 1


@pytest.mark.asyncio
async def test_forecast_week_creates_yield_forecast(db_session, tenant_farm_aoi):
    from worker.jobs import forecast_week as forecast_job

    db_session.execute(
        text("""
            INSERT INTO seasons (
                tenant_id, aoi_id, season_year, start_date, end_date,
                crop_type, planted_date, expected_harvest_date, status
            )
            VALUES (
                :tenant_id, :aoi_id, :season_year, :start_date, :end_date,
                'CORN', :planted, :harvest, 'ACTIVE'
            )
        """),
        {
            "tenant_id": tenant_farm_aoi["tenant_id"],
            "aoi_id": tenant_farm_aoi["aoi_id"],
            "season_year": 2024,
            "start_date": date(2023, 10, 1),
            "end_date": None,
            "planted": date(2023, 10, 1),
            "harvest": date(2024, 3, 15),
        },
    )
    db_session.execute(
        text("""
            INSERT INTO observations_weekly
            (tenant_id, aoi_id, year, week, pipeline_version, status, valid_pixel_ratio,
             ndvi_mean, ndvi_p10, ndvi_p50, ndvi_p90, ndvi_std, baseline, anomaly)
            VALUES
            (:tenant_id, :aoi_id, 2024, 1, 'v1', 'OK', 0.8, 0.6, 0.5, 0.6, 0.7, 0.05, 0.6, 0.01),
            (:tenant_id, :aoi_id, 2024, 2, 'v1', 'OK', 0.8, 0.62, 0.52, 0.62, 0.72, 0.05, 0.6, 0.01),
            (:tenant_id, :aoi_id, 2024, 3, 'v1', 'OK', 0.8, 0.64, 0.54, 0.64, 0.74, 0.05, 0.6, 0.01),
            (:tenant_id, :aoi_id, 2024, 4, 'v1', 'OK', 0.8, 0.66, 0.56, 0.66, 0.76, 0.05, 0.6, 0.01)
        """),
        {"tenant_id": tenant_farm_aoi["tenant_id"], "aoi_id": tenant_farm_aoi["aoi_id"]},
    )
    db_session.commit()

    job_id = _insert_job(
        db_session,
        tenant_farm_aoi["tenant_id"],
        tenant_farm_aoi["aoi_id"],
        "FORECAST_WEEK",
        {"tenant_id": tenant_farm_aoi["tenant_id"], "aoi_id": tenant_farm_aoi["aoi_id"], "year": 2024, "week": 4},
    )

    result = await forecast_job.handle_forecast_week(
        {
            "id": job_id,
            "tenant_id": tenant_farm_aoi["tenant_id"],
            "aoi_id": tenant_farm_aoi["aoi_id"],
            "payload": {"year": 2024, "week": 4},
        },
        db_session,
    )

    assert result["estimated_yield_kg_ha"] > 0
    forecast_count = db_session.execute(
        text("""
            SELECT COUNT(*)
            FROM yield_forecasts
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id AND year = 2024 AND week = 4
        """),
        {"tenant_id": tenant_farm_aoi["tenant_id"], "aoi_id": tenant_farm_aoi["aoi_id"]},
    ).scalar_one()
    assert forecast_count == 1
