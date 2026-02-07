import sys
import types
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[1]
WORKER_PATH = ROOT / "services" / "worker"
if str(WORKER_PATH) not in sys.path:
    sys.path.insert(0, str(WORKER_PATH))


def _ensure_optional_modules():
    if "rasterio" not in sys.modules:
        rasterio_stub = types.ModuleType("rasterio")
        sys.modules["rasterio"] = rasterio_stub
    if "rasterio.mask" not in sys.modules:
        mask_stub = types.ModuleType("rasterio.mask")
        mask_stub.mask = lambda *args, **kwargs: None
        sys.modules["rasterio.mask"] = mask_stub
    if "shapely" not in sys.modules:
        shapely_stub = types.ModuleType("shapely")
        geometry_stub = types.ModuleType("shapely.geometry")
        geometry_stub.shape = lambda geom: geom
        geometry_stub.mapping = lambda geom: geom
        shapely_stub.geometry = geometry_stub
        sys.modules["shapely"] = shapely_stub
        sys.modules["shapely.geometry"] = geometry_stub


def _ensure_webhook_tables(db) -> None:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS tenant_webhooks (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            url text NOT NULL,
            secret text NULL,
            events jsonb NOT NULL DEFAULT '[]'::jsonb,
            status text NOT NULL DEFAULT 'ACTIVE',
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """))
    db.execute(text("""
        ALTER TABLE tenant_webhooks
            ADD COLUMN IF NOT EXISTS status text,
            ADD COLUMN IF NOT EXISTS events jsonb,
            ADD COLUMN IF NOT EXISTS secret text
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS tenant_event_outbox (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            webhook_id uuid NULL REFERENCES tenant_webhooks(id) ON DELETE SET NULL,
            event_type text NOT NULL,
            payload jsonb NOT NULL,
            status text NOT NULL DEFAULT 'PENDING',
            retry_count int NOT NULL DEFAULT 0,
            error_message text NULL,
            http_status int NULL,
            delivered_at timestamptz NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """))
    db.execute(text("""
        ALTER TABLE tenant_event_outbox
            ADD COLUMN IF NOT EXISTS webhook_id uuid,
            ADD COLUMN IF NOT EXISTS payload jsonb,
            ADD COLUMN IF NOT EXISTS retry_count int,
            ADD COLUMN IF NOT EXISTS error_message text,
            ADD COLUMN IF NOT EXISTS http_status int,
            ADD COLUMN IF NOT EXISTS delivered_at timestamptz
    """))
    db.commit()


@pytest.fixture
def db_session():
    from app.database import SessionLocal

    session = SessionLocal()
    _ensure_webhook_tables(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def tenant_id(db_session):
    tenant_id = uuid.uuid4()
    db_session.execute(
        text("""
            INSERT INTO tenants (id, type, name, status, plan, quotas)
            VALUES (:id, 'COMPANY', 'Webhook Tenant', 'ACTIVE', 'BASIC', '{}'::jsonb)
        """),
        {"id": str(tenant_id)},
    )
    db_session.commit()
    try:
        yield str(tenant_id)
    finally:
        db_session.execute(
            text("DELETE FROM tenants WHERE id = :tenant_id"),
            {"tenant_id": str(tenant_id)},
        )
        db_session.commit()


@pytest.mark.asyncio
async def test_stac_search_scenes_maps_assets(monkeypatch):
    _ensure_optional_modules()
    from worker.pipeline.providers import planetary_computer as pc

    class Asset:
        def __init__(self, href):
            self.href = href

    class FakeItem:
        def __init__(self):
            self.id = "item-1"
            self.collection_id = "sentinel-2-l2a"
            self.datetime = datetime(2024, 1, 1)
            self.properties = {"eo:cloud_cover": 12.0, "platform": "sentinel-2"}
            self.assets = {
                "B04": Asset("s3://red"),
                "B03": Asset("s3://green"),
                "B02": Asset("s3://blue"),
                "B08": Asset("s3://nir"),
                "B11": Asset("s3://swir"),
                "B12": Asset("s3://swir2"),
                "B05": Asset("s3://rededge"),
                "SCL": Asset("s3://scl"),
            }
            self.bbox = [-1, -1, 1, 1]
            self.geometry = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]} 

    class FakeSearch:
        def items(self):
            return [FakeItem()]

    class FakeClient:
        def search(self, **kwargs):  # noqa: ANN001
            return FakeSearch()

    class DummyClient:
        @staticmethod
        def open(*args, **kwargs):  # noqa: ANN001
            return FakeClient()

    class FakeGeom:
        def __init__(self, geom):
            self._geom = geom
            self.bounds = (-1, -1, 1, 1)

    monkeypatch.setattr(pc, "Client", DummyClient)
    monkeypatch.setattr(pc, "shape", lambda geom: FakeGeom(geom))
    monkeypatch.setattr(pc, "mapping", lambda geom: geom._geom if hasattr(geom, "_geom") else geom)

    client = pc.PlanetaryComputerProvider(catalog_url="http://example.com")
    scenes = await client.search_scenes(
        aoi_geom={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 2),
        max_cloud_cover=20.0,
    )

    assert len(scenes) == 1
    scene = scenes[0]
    assert scene["cloud_cover"] == 12.0
    assert scene["assets"]["red"] == "s3://red"
    assert scene["assets"]["nir"] == "s3://nir"


@pytest.mark.asyncio
async def test_webhook_outbox_delivered(db_session, tenant_id, monkeypatch):
    from app.infrastructure import webhooks

    webhook_id = db_session.execute(
        text("""
            INSERT INTO tenant_webhooks (tenant_id, url, secret, events, status)
            VALUES (:tenant_id, 'https://example.com/webhook', 'secret', :events, 'ACTIVE')
            RETURNING id
        """),
        {"tenant_id": tenant_id, "events": '["signal.created"]'},
    ).fetchone()[0]
    db_session.commit()

    class DummyResponse:
        status_code = 204

        def raise_for_status(self):
            return None

    class DummyClient:
        def __init__(self, *args, **kwargs):  # noqa: ANN001
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):  # noqa: ANN001
            return None

        async def post(self, *args, **kwargs):  # noqa: ANN001
            return DummyResponse()

    monkeypatch.setattr(webhooks.httpx, "AsyncClient", DummyClient)

    await webhooks.execute_webhook(
        tenant_id=tenant_id,
        event_type="signal.created",
        payload={"signal_id": "sig-1"},
        db=db_session,
    )

    outbox = db_session.execute(
        text("""
            SELECT status, http_status, webhook_id
            FROM tenant_event_outbox
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"tenant_id": tenant_id},
    ).fetchone()

    assert outbox.status == "DELIVERED"
    assert outbox.http_status == 204
    assert str(outbox.webhook_id) == str(webhook_id)


def test_ai_provider_factory_with_stubs(monkeypatch):
    from app.ai_assistant import providers

    class DummyOpenAI:
        def __init__(self, api_key):  # noqa: ANN001
            self.api_key = api_key
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))

        def _create(self, **kwargs):  # noqa: ANN001
            message = types.SimpleNamespace(content="ok", tool_calls=None)
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])

    openai_module = types.ModuleType("openai")
    openai_module.OpenAI = DummyOpenAI
    monkeypatch.setitem(sys.modules, "openai", openai_module)

    class DummyAnthropic:
        def __init__(self, api_key):  # noqa: ANN001
            self.api_key = api_key
            self.messages = types.SimpleNamespace(create=self._create)

        def _create(self, **kwargs):  # noqa: ANN001
            block = types.SimpleNamespace(type="text", text="ok")
            return types.SimpleNamespace(content=[block])

    anthropic_module = types.ModuleType("anthropic")
    anthropic_module.Anthropic = DummyAnthropic
    monkeypatch.setitem(sys.modules, "anthropic", anthropic_module)

    class DummyChat:
        def send_message(self, *args, **kwargs):  # noqa: ANN001
            return types.SimpleNamespace(text="ok")

    class DummyModel:
        def __init__(self, *args, **kwargs):  # noqa: ANN001
            pass

        def start_chat(self, history=None):  # noqa: ANN001
            return DummyChat()

    genai_module = types.ModuleType("google.generativeai")
    genai_module.configure = lambda **kwargs: None
    genai_module.GenerativeModel = DummyModel
    monkeypatch.setitem(sys.modules, "google.generativeai", genai_module)

    openai_provider = providers.create_provider("openai", "key")
    assert openai_provider.generate([providers.Message("user", "hi")]) == "ok"

    anthropic_provider = providers.create_provider("anthropic", "key")
    assert anthropic_provider.generate([providers.Message("user", "hi")]) == "ok"

    gemini_provider = providers.create_provider("gemini", "key")
    assert gemini_provider.generate([providers.Message("user", "hi")]) == "ok"
