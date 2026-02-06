import asyncio
import importlib
import os
import sys
import uuid
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

import boto3
import pytest


ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "services" / "api"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))


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
def api_settings(localstack_endpoint: str):
    _disable_proxies()
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured for integration tests")

    suffix = uuid.uuid4().hex[:8]
    queue_name = f"vivacampo-api-jobs-test-{suffix}"

    os.environ["AWS_ENDPOINT_URL"] = localstack_endpoint
    os.environ.setdefault("AWS_REGION", "sa-east-1")
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
    os.environ.setdefault("S3_BUCKET", "vivacampo-derived-local")
    os.environ.setdefault("S3_FORCE_PATH_STYLE", "true")
    os.environ["SQS_QUEUE_NAME"] = queue_name
    os.environ.setdefault("SQS_DLQ_NAME", f"{queue_name}-dlq")
    os.environ.setdefault("DATABASE_URL", os.environ["DATABASE_URL"])

    import app.config as app_config
    import app.infrastructure.s3_client as s3_client
    import app.infrastructure.sqs_client as sqs_client
    import app.infrastructure.adapters.storage.s3_adapter as s3_adapter
    import app.infrastructure.adapters.message_queue.sqs_adapter as sqs_adapter

    importlib.reload(app_config)
    importlib.reload(s3_client)
    importlib.reload(sqs_client)
    importlib.reload(s3_adapter)
    importlib.reload(sqs_adapter)

    return app_config.settings


@pytest.fixture(scope="session")
def ensure_bucket(localstack_endpoint: str) -> str:
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


@pytest.fixture(scope="session")
def ensure_queue(localstack_endpoint: str, api_settings):
    _disable_proxies()
    client = boto3.client(
        "sqs",
        region_name=os.environ.get("AWS_REGION", "sa-east-1"),
        endpoint_url=localstack_endpoint,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
    )
    client.create_queue(QueueName=os.environ["SQS_QUEUE_NAME"])


@pytest.mark.asyncio
async def test_api_s3_adapter_roundtrip(api_settings, ensure_bucket):
    from app.infrastructure.adapters.storage.s3_adapter import S3Adapter

    adapter = S3Adapter()
    key = f"tests/{uuid.uuid4().hex}.bin"
    payload = b"vivacampo-api-s3"

    uri = await adapter.upload(key=key, data=payload, content_type="application/octet-stream")
    assert uri.endswith(key)
    assert await adapter.exists(key) is True
    downloaded = await adapter.download(key)
    assert downloaded == payload


@pytest.mark.asyncio
async def test_api_sqs_adapter_publish_consume(api_settings, ensure_queue):
    from app.infrastructure.adapters.message_queue.sqs_adapter import SQSAdapter

    adapter = SQSAdapter()
    message_id = uuid.uuid4().hex
    await adapter.publish(os.environ["SQS_QUEUE_NAME"], {"type": "PING", "id": message_id})

    received = []

    async def handler(message):  # noqa: ANN001
        received.append(message.body)

    await adapter.consume(os.environ["SQS_QUEUE_NAME"], handler, max_messages=1, wait_time_seconds=1)
    assert received
    assert any(msg.get("id") == message_id for msg in received)
