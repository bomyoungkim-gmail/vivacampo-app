"""Weather use cases."""
from __future__ import annotations

import hashlib
import json

from app.application.decorators import require_tenant
from app.application.dtos.weather import WeatherHistoryCommand, WeatherSyncCommand, WeatherSyncResult
from app.domain.ports.job_repository import IJobRepository
from app.domain.ports.message_queue import IMessageQueue
from app.domain.ports.weather_data_repository import IWeatherDataRepository


class GetWeatherHistoryUseCase:
    def __init__(self, repo: IWeatherDataRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: WeatherHistoryCommand) -> list[dict]:
        return await self.repo.get_history(
            tenant_id=command.tenant_id,
            aoi_id=command.aoi_id,
            start_date=command.start_date,
            end_date=command.end_date,
            limit=command.limit,
        )


class RequestWeatherSyncUseCase:
    def __init__(self, job_repo: IJobRepository, queue: IMessageQueue, queue_name: str):
        self.job_repo = job_repo
        self.queue = queue
        self.queue_name = queue_name

    @require_tenant
    async def execute(self, command: WeatherSyncCommand) -> WeatherSyncResult:
        job_key = hashlib.sha256(
            f"{command.tenant_id.value}{command.aoi_id}WEATHER_SYNC".encode()
        ).hexdigest()

        payload = {
            "tenant_id": str(command.tenant_id.value),
            "aoi_id": str(command.aoi_id),
        }

        job_id = await self.job_repo.create_weather_sync_job(
            tenant_id=command.tenant_id,
            aoi_id=command.aoi_id,
            job_key=job_key,
            payload_json=json.dumps(payload),
        )

        message_body = {
            "job_id": str(job_id),
            "job_type": "PROCESS_WEATHER",
            "payload": payload,
        }

        await self.queue.publish(self.queue_name, message_body)

        return WeatherSyncResult(job_id=job_id, status="PENDING", message="Weather sync started")
