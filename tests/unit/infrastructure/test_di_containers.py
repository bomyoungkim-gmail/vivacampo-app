import pytest

from app.infrastructure.di_container import ApiContainer

planetary_computer = pytest.importorskip("planetary_computer")
from worker.infrastructure.di_container import WorkerContainer


def test_api_container_provides_use_cases():
    container = ApiContainer(env="local", local_storage_base="/tmp")
    assert container.message_queue() is not None
    assert container.object_storage(force_local=True) is not None


def test_worker_container_provides_satellite_provider():
    container = WorkerContainer(env="local")
    provider = container.satellite_provider()
    assert provider is not None
