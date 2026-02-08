import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.auth.dependencies import CurrentMembership, get_current_membership, get_current_tenant_id
from app.infrastructure.di_container import get_container


class DummyAuditLogger:
    def __init__(self):
        self.events = []

    def log(self, **kwargs):
        self.events.append(kwargs)


class DummyAdoptionUseCase:
    async def execute(self, command):
        return {
            "events": [
                {"event_name": "onboarding_step", "count": 2, "last_seen": "2026-02-07T12:00:00Z"},
            ],
            "phases": [
                {"phase": "F1", "count": 2},
            ],
        }


class DummyContainer:
    def __init__(self):
        self.audit_logger_instance = DummyAuditLogger()

    def audit_logger(self):
        return self.audit_logger_instance

    def adoption_metrics_use_case(self):
        return DummyAdoptionUseCase()


def override_get_container():
    return DummyContainer()


def override_membership_editor():
    return CurrentMembership(
        identity_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        role="EDITOR",
    )


def override_membership_admin():
    return CurrentMembership(
        identity_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        role="TENANT_ADMIN",
    )


def override_tenant_id():
    return uuid.uuid4()


def test_track_analytics_event():
    app.dependency_overrides[get_container] = override_get_container
    app.dependency_overrides[get_current_membership] = override_membership_editor
    app.dependency_overrides[get_current_tenant_id] = override_tenant_id

    client = TestClient(app)
    response = client.post("/v1/app/analytics/events", json={"event_name": "onboarding_step"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    app.dependency_overrides.clear()


def test_get_adoption_metrics():
    app.dependency_overrides[get_container] = override_get_container
    app.dependency_overrides[get_current_membership] = override_membership_admin
    app.dependency_overrides[get_current_tenant_id] = override_tenant_id

    client = TestClient(app)
    response = client.get("/v1/app/analytics/adoption")
    assert response.status_code == 200
    payload = response.json()
    assert payload["events"][0]["event_name"] == "onboarding_step"
    assert payload["phases"][0]["phase"] == "F1"

    app.dependency_overrides.clear()
