from fastapi.testclient import TestClient

from uuid import uuid4

from app.main import app
from app.auth.dependencies import CurrentMembership, get_current_membership
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request


client = TestClient(app)


def test_validation_error_shape():
    app.dependency_overrides[get_current_membership] = lambda: CurrentMembership(
        identity_id=uuid4(),
        tenant_id=uuid4(),
        membership_id=uuid4(),
        role="VIEWER",
    )
    resp = client.get("/v1/tiles/aois/not-a-uuid/tilejson.json")
    app.dependency_overrides.pop(get_current_membership, None)
    assert resp.status_code == 422
    payload = resp.json()
    assert "error" in payload
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert "errors" in payload["error"].get("details", {})


def test_http_exception_shape():
    # Missing auth should trigger HTTPException from dependency
    resp = client.get("/v1/app/farms")
    assert resp.status_code in (401, 403)
    payload = resp.json()
    assert "error" in payload
    assert "code" in payload["error"]
    assert "message" in payload["error"]


def test_rate_limit_handler_shape():
    scope = {"type": "http", "method": "GET", "path": "/"}
    request = Request(scope)
    request.state.request_id = "test-trace"
    handler = app.exception_handlers[RateLimitExceeded]
    import asyncio
    class _Limit:
        error_message = "limit"

        def __str__(self):
            return "limit"

    response = asyncio.run(handler(request, RateLimitExceeded(_Limit())))
    assert response.status_code == 429
    import json
    payload = json.loads(response.body.decode())
    assert payload["error"]["code"] == "TOO_MANY_REQUESTS"
    assert payload["error"]["traceId"] == "test-trace"
