import importlib
import os
import sys
import uuid
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

import boto3
import pytest
from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[1]
WORKER_PATH = ROOT / "services" / "worker"
if str(WORKER_PATH) not in sys.path:
    sys.path.insert(0, str(WORKER_PATH))


def _disable_proxies() -> None:
    os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1,localstack")
    os.environ.setdefault("no_proxy", "localhost,127.0.0.1,localstack")
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)
    os.environ.pop("http_proxy", None)
    os.environ.pop("https_proxy", None)


def _localstack_health_ok(endpoint: str) -> bool:
    _disable_proxies()
    try:
        opener = build_opener(ProxyHandler({}))
        with opener.open(f"{endpoint}/_localstack/health", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def localstack_endpoint() -> str:
    endpoint = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")

    if os.name == "nt" and "localstack" in endpoint:
        endpoint = "http://localhost:4566"

    if _localstack_health_ok(endpoint):
        return endpoint

    if "localstack" in endpoint:
        fallback = "http://localhost:4566"
        if _localstack_health_ok(fallback):
            return fallback

    pytest.skip("LocalStack not available on AWS_ENDPOINT_URL or localhost:4566")


@pytest.fixture(scope="session")
def worker_settings(localstack_endpoint: str):
    _disable_proxies()
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured for integration tests")
    suffix = uuid.uuid4().hex[:8]
    queue_name = f"vivacampo-jobs-test-{suffix}"
    dlq_name = f"vivacampo-jobs-dlq-test-{suffix}"
    os.environ["AWS_ENDPOINT_URL"] = localstack_endpoint
    os.environ.setdefault("AWS_REGION", "sa-east-1")
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
    os.environ.setdefault("S3_BUCKET", "vivacampo-derived-local")
    os.environ.setdefault("S3_FORCE_PATH_STYLE", "true")
    os.environ["SQS_QUEUE_NAME"] = queue_name
    os.environ["SQS_DLQ_NAME"] = dlq_name
    os.environ.setdefault("DATABASE_URL", os.environ["DATABASE_URL"])

    import worker.config as worker_config
    import worker.shared.aws_clients as aws_clients

    importlib.reload(worker_config)
    importlib.reload(aws_clients)

    return worker_config.settings, aws_clients


@pytest.fixture(scope="session")
def ensure_localstack_bucket(localstack_endpoint: str) -> str:
    _disable_proxies()
    bucket = os.environ.get("S3_BUCKET", "vivacampo-derived-local")
    client = boto3.client(
        "s3",
        region_name=os.environ.get("AWS_REGION", "sa-east-1"),
        endpoint_url=localstack_endpoint,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
        config=boto3.session.Config(s3={"addressing_style": "path"}),
    )
    try:
        client.head_bucket(Bucket=bucket)
    except Exception:
        client.create_bucket(Bucket=bucket)
    return bucket


def test_s3_client_upload_and_get_json(worker_settings, ensure_localstack_bucket):
    _, aws_clients = worker_settings
    s3 = aws_clients.S3Client()

    key = f"tests/{uuid.uuid4().hex}.json"
    payload = {"hello": "world", "id": uuid.uuid4().hex}

    uri = s3.upload_json(key, payload)
    assert uri.endswith(key)
    assert s3.object_exists(key) is True
    loaded = s3.get_json(key)
    assert loaded == payload


def test_sqs_client_send_receive_delete(worker_settings):
    _, aws_clients = worker_settings
    sqs = aws_clients.SQSClient()

    message_id = uuid.uuid4().hex
    sqs.send_message({"type": "PING", "id": message_id})
    messages = sqs.receive_messages(max_messages=1, wait_time=1)

    assert messages
    message = messages[0]
    assert "ReceiptHandle" in message
    assert message_id in message.get("Body", "")

    sqs.delete_message(message["ReceiptHandle"])


def test_sql_job_repository_upsert_and_mark_status(worker_settings):
    from app.database import SessionLocal
    from worker.infrastructure.adapters.jobs.sql_job_repository import SqlJobRepository

    session = SessionLocal()
    try:
        tenant_id = str(uuid.uuid4())
        farm_id = str(uuid.uuid4())
        aoi_id = str(uuid.uuid4())

        session.execute(
            text("""
                INSERT INTO tenants (id, type, name, status, plan, quotas)
                VALUES (:id, 'COMPANY', 'Integration Tenant', 'ACTIVE', 'BASIC', '{}'::jsonb)
            """),
            {"id": tenant_id},
        )
        session.execute(
            text("""
                INSERT INTO farms (id, tenant_id, name, timezone)
                VALUES (:id, :tenant_id, 'Integration Farm', 'America/Sao_Paulo')
            """),
            {"id": farm_id, "tenant_id": tenant_id},
        )
        session.execute(
            text("""
                INSERT INTO aois (id, tenant_id, farm_id, name, use_type, status, geom, area_ha)
                VALUES (
                    :id, :tenant_id, :farm_id, 'Integration AOI', 'CROP', 'ACTIVE',
                    ST_GeomFromText(:geom, 4326), :area_ha
                )
            """),
            {
                "id": aoi_id,
                "tenant_id": tenant_id,
                "farm_id": farm_id,
                "geom": "MULTIPOLYGON(((-47.0 -23.0, -47.0 -23.1, -47.1 -23.1, -47.1 -23.0, -47.0 -23.0)))",
                "area_ha": 10.0,
            },
        )
        session.commit()

        repo = SqlJobRepository(session)
        job_id = repo.upsert_job(
            tenant_id=tenant_id,
            aoi_id=aoi_id,
            job_type="PROCESS_WEEK",
            job_key=f"it-{uuid.uuid4().hex}",
            payload={"tenant_id": tenant_id, "aoi_id": aoi_id, "year": 2024, "week": 1},
        )
        repo.commit()
        assert job_id is not None

        repo.mark_status(job_id, "RUNNING")
        repo.commit()
        status = session.execute(
            text("SELECT status FROM jobs WHERE id = :job_id"),
            {"job_id": job_id},
        ).scalar_one()
        assert status == "RUNNING"
    finally:
        session.execute(text("DELETE FROM tenants WHERE id = :tenant_id"), {"tenant_id": tenant_id})
        session.commit()
        session.close()
