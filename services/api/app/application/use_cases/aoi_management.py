"""AOI management use cases (update/delete/backfill/assets/history)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Tuple

from app.application.decorators import require_tenant
from app.application.dtos.aoi_management import (
    AoiAssetsCommand,
    AoiHistoryCommand,
    BackfillResult,
    DeleteAoiCommand,
    RequestBackfillCommand,
    UpdateAoiCommand,
    UpdateAoiResult,
)
from app.domain.ports.aoi_data_repository import IAoiDataRepository
from app.domain.ports.aoi_repository import IAOIRepository
from app.domain.ports.job_repository import IJobRepository
from app.domain.ports.message_queue import IMessageQueue
from app.domain.value_objects.geometry_wkt import GeometryWkt
from app.domain.value_objects.area_hectares import AreaHectares


class UpdateAoiUseCase:
    def __init__(self, repo: IAOIRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: UpdateAoiCommand) -> UpdateAoiResult | None:
        geometry_changed = command.geometry_wkt is not None
        updated = await self.repo.update(
            tenant_id=command.tenant_id,
            aoi_id=command.aoi_id,
            name=command.name,
            use_type=command.use_type,
            status=command.status,
            geometry_wkt=command.geometry_wkt,
        )
        if not updated:
            return None

        # Validate geometry + area via value objects
        geom = GeometryWkt(value=updated.geometry_wkt.value)
        area = AreaHectares(value=updated.area_hectares.value)

        return UpdateAoiResult(
            id=updated.id,
            farm_id=updated.farm_id,
            name=updated.name,
            use_type=updated.use_type,
            status=updated.status,
            area_ha=area.value,
            geometry=geom.value,
            created_at=updated.created_at,
            geometry_changed=geometry_changed,
        )


class DeleteAoiUseCase:
    def __init__(self, repo: IAOIRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: DeleteAoiCommand) -> bool:
        return await self.repo.delete(command.tenant_id, command.aoi_id)


class AoiAssetsUseCase:
    def __init__(self, repo: IAoiDataRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: AoiAssetsCommand) -> dict:
        return await self.repo.get_latest_assets(command.tenant_id, command.aoi_id)


class AoiHistoryUseCase:
    def __init__(self, repo: IAoiDataRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: AoiHistoryCommand) -> list[dict]:
        return await self.repo.get_history(command.tenant_id, command.aoi_id, command.limit)


class RequestBackfillUseCase:
    def __init__(self, job_repo: IJobRepository, queue: IMessageQueue, queue_name: str, pipeline_version: str):
        self.job_repo = job_repo
        self.queue = queue
        self.queue_name = queue_name
        self.pipeline_version = pipeline_version

    @require_tenant
    async def execute(self, command: RequestBackfillCommand) -> BackfillResult:
        from_dt = datetime.strptime(command.from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(command.to_date, "%Y-%m-%d")
        weeks_count = int((to_dt - from_dt).days / 7) + 1

        job_key = hashlib.sha256(
            f"{command.tenant_id.value}{command.aoi_id}{command.from_date}{command.to_date}BACKFILL{self.pipeline_version}".encode()
        ).hexdigest()

        payload = {
            "tenant_id": str(command.tenant_id.value),
            "aoi_id": str(command.aoi_id),
            "from_date": command.from_date,
            "to_date": command.to_date,
            "cadence": command.cadence,
        }

        job_id = await self.job_repo.create_backfill_job(
            tenant_id=command.tenant_id,
            aoi_id=command.aoi_id,
            job_key=job_key,
            payload_json=json.dumps(payload),
        )

        message_body = {
            "job_id": str(job_id),
            "job_type": "BACKFILL",
            "payload": payload,
        }

        await self.queue.publish(self.queue_name, message_body)

        return BackfillResult(
            job_id=job_id,
            status="PENDING",
            weeks_count=weeks_count,
            message="Backfill job created successfully",
        )
