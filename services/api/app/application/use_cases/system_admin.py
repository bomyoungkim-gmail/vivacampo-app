"""System admin use cases."""
from __future__ import annotations

from datetime import date, timedelta
import hashlib
import json

from app.application.decorators import require_tenant
from app.application.dtos.system_admin import (
    CreateTenantCommand,
    GlobalAuditLogCommand,
    ListMissingWeeksCommand,
    ListSystemJobsCommand,
    ListTenantsCommand,
    ReprocessMissingAoisCommand,
    ReprocessMissingWeeksCommand,
    RetryJobCommand,
    UpdateTenantCommand,
    ReprocessJobsCommand,
)
from app.application.dtos.aoi_management import RequestBackfillCommand
from app.application.use_cases.aoi_management import RequestBackfillUseCase
from app.domain.ports.system_admin_repository import ISystemAdminRepository
from app.domain.ports.job_repository import IJobRepository
from app.domain.ports.message_queue import IMessageQueue
from app.domain.value_objects.tenant_id import TenantId


class ListTenantsUseCase:
    def __init__(self, repo: ISystemAdminRepository):
        self.repo = repo

    async def execute(self, command: ListTenantsCommand) -> list[dict]:
        return await self.repo.list_tenants(command.tenant_type, command.limit)


class CreateTenantUseCase:
    def __init__(self, repo: ISystemAdminRepository):
        self.repo = repo

    async def execute(self, command: CreateTenantCommand) -> dict:
        return await self.repo.create_tenant(command.name, command.tenant_type)


class UpdateTenantUseCase:
    def __init__(self, repo: ISystemAdminRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: UpdateTenantCommand) -> dict | None:
        current = await self.repo.get_tenant_status(command.tenant_id)
        if current is None:
            return None
        await self.repo.update_tenant_status(command.tenant_id, command.status)
        return {"before": current, "after": command.status}


class ListSystemJobsUseCase:
    def __init__(self, repo: ISystemAdminRepository):
        self.repo = repo

    async def execute(self, command: ListSystemJobsCommand) -> list[dict]:
        return await self.repo.list_jobs(command.status, command.job_type, command.limit)


class RetryJobUseCase:
    def __init__(self, repo: ISystemAdminRepository):
        self.repo = repo

    async def execute(self, command: RetryJobCommand) -> bool:
        return await self.repo.retry_job(command.job_id)


class ReprocessMissingAoisUseCase:
    def __init__(self, repo: ISystemAdminRepository, job_repo: IJobRepository, queue: IMessageQueue, queue_name: str, pipeline_version: str):
        self.repo = repo
        self.job_repo = job_repo
        self.queue = queue
        self.queue_name = queue_name
        self.pipeline_version = pipeline_version

    async def execute(self, command: ReprocessMissingAoisCommand) -> dict:
        to_date = date.today().isoformat()
        from_date = (date.today() - timedelta(days=command.days)).isoformat()

        rows = await self.repo.list_missing_aois(command.limit)
        if not rows:
            return {"queued": 0, "message": "No missing AOIs found"}

        queued = 0
        for row in rows:
            tenant_id = TenantId(value=row["tenant_id"])
            aoi_id = row["id"]

            job_key = hashlib.sha256(
                f"{tenant_id.value}{aoi_id}{from_date}{to_date}BACKFILL{self.pipeline_version}".encode()
            ).hexdigest()

            payload = {
                "tenant_id": str(tenant_id.value),
                "aoi_id": str(aoi_id),
                "from_date": from_date,
                "to_date": to_date,
                "cadence": "weekly",
            }

            job_id = await self.job_repo.create_backfill_job(
                tenant_id=tenant_id,
                aoi_id=aoi_id,
                job_key=job_key,
                payload_json=json.dumps(payload),
            )

            await self.queue.publish(
                self.queue_name,
                {
                    "job_id": str(job_id),
                    "job_type": "BACKFILL",
                    "payload": payload,
                },
            )
            queued += 1

        return {"queued": queued, "from_date": from_date, "to_date": to_date}


class ListMissingWeeksUseCase:
    def __init__(self, repo: ISystemAdminRepository):
        self.repo = repo

    async def execute(self, command: ListMissingWeeksCommand) -> dict:
        today = date.today()
        start = today - timedelta(weeks=command.weeks - 1)

        expected_weeks = []
        cursor = start
        while cursor <= today:
            iso = cursor.isocalendar()
            expected_weeks.append((iso.year, iso.week))
            cursor += timedelta(days=7)

        aois = await self.repo.list_active_aois(command.limit)
        results = []
        for row in aois:
            existing = await self.repo.list_observation_weeks(row["tenant_id"], row["id"])
            existing_set = set(existing)
            missing = [(y, w) for (y, w) in expected_weeks if (y, w) not in existing_set]
            if missing:
                results.append(
                    {
                        "tenant_id": str(row["tenant_id"]),
                        "aoi_id": str(row["id"]),
                        "farm_name": row.get("farm_name"),
                        "aoi_name": row.get("aoi_name"),
                        "missing_weeks": missing,
                        "missing_count": len(missing),
                    }
                )

        return {"weeks": command.weeks, "items": results}


class ReprocessMissingWeeksUseCase:
    def __init__(self, repo: ISystemAdminRepository, backfill_use_case: RequestBackfillUseCase):
        self.repo = repo
        self.backfill_use_case = backfill_use_case

    async def execute(self, command: ReprocessMissingWeeksCommand) -> dict:
        today = date.today()
        start = today - timedelta(weeks=command.weeks - 1)

        expected_weeks = []
        cursor = start
        while cursor <= today:
            iso = cursor.isocalendar()
            expected_weeks.append((iso.year, iso.week))
            cursor += timedelta(days=7)

        aois = await self.repo.list_active_aois(command.limit)
        queued = 0

        for row in aois:
            existing = await self.repo.list_observation_weeks(row["tenant_id"], row["id"])
            existing_set = set(existing)
            missing = [(y, w) for (y, w) in expected_weeks if (y, w) not in existing_set]

            if not missing:
                continue

            runs = []
            current = [missing[0]]
            for (y, w) in missing[1:]:
                prev_y, prev_w = current[-1]
                prev_end = date.fromisocalendar(prev_y, prev_w, 7)
                this_start = date.fromisocalendar(y, w, 1)
                if this_start == prev_end + timedelta(days=1):
                    current.append((y, w))
                else:
                    runs.append(current)
                    current = [(y, w)]
            runs.append(current)

            for run in runs[: command.max_runs_per_aoi]:
                from_date = date.fromisocalendar(run[0][0], run[0][1], 1).isoformat()
                to_date = date.fromisocalendar(run[-1][0], run[-1][1], 7).isoformat()

                await self.backfill_use_case.execute(
                    RequestBackfillCommand(
                        tenant_id=TenantId(value=row["tenant_id"]),
                        aoi_id=row["id"],
                        from_date=from_date,
                        to_date=to_date,
                        cadence="weekly",
                    )
                )
                queued += 1

        return {"queued": queued, "weeks": command.weeks, "limit": command.limit}


class SystemHealthUseCase:
    def __init__(self, repo: ISystemAdminRepository):
        self.repo = repo

    async def execute(self) -> dict:
        ok, error = await self.repo.check_db()
        db_status = "healthy" if ok else f"unhealthy: {error}"
        stats = await self.repo.get_job_stats_24h()
        return {
            "status": "healthy" if ok else "degraded",
            "database": db_status,
            "jobs_24h": stats,
        }


class QueueStatsUseCase:
    def __init__(self, repo: ISystemAdminRepository):
        self.repo = repo

    async def execute(self) -> dict:
        return await self.repo.get_queue_stats()


class GlobalAuditLogUseCase:
    def __init__(self, repo: ISystemAdminRepository):
        self.repo = repo

    async def execute(self, command: GlobalAuditLogCommand) -> list[dict]:
        return await self.repo.list_audit_logs(command.limit)


class ReprocessJobsUseCase:
    def __init__(self, job_repo: IJobRepository, queue: IMessageQueue, queue_name: str, pipeline_version: str):
        self.job_repo = job_repo
        self.queue = queue
        self.queue_name = queue_name
        self.pipeline_version = pipeline_version

    async def execute(self, command: ReprocessJobsCommand) -> dict:
        allowed = {
            "PROCESS_WEEK",
            "PROCESS_RADAR_WEEK",
            "PROCESS_TOPOGRAPHY",
            "PROCESS_WEATHER",
            "ALERTS_WEEK",
            "SIGNALS_WEEK",
            "FORECAST_WEEK",
            "BACKFILL",
            "CALCULATE_STATS",
            "WARM_CACHE",
            "DETECT_HARVEST",
        }
        job_types = [jt for jt in command.job_types if jt in allowed]
        if not job_types:
            raise ValueError("No valid job_types provided")

        aoi_required = {
            "PROCESS_WEEK",
            "PROCESS_RADAR_WEEK",
            "PROCESS_TOPOGRAPHY",
            "PROCESS_WEATHER",
            "ALERTS_WEEK",
            "SIGNALS_WEEK",
            "FORECAST_WEEK",
            "BACKFILL",
            "CALCULATE_STATS",
            "WARM_CACHE",
            "DETECT_HARVEST",
        }
        if any(jt in aoi_required for jt in job_types) and not command.aoi_id:
            raise ValueError("aoi_id is required for requested job_types")

        results = []
        tenant_id = TenantId(value=command.tenant_id)
        for job_type in job_types:
            job_key = hashlib.sha256(
                f"{tenant_id.value}{command.aoi_id}{command.year}{command.week}{job_type}{self.pipeline_version}".encode()
            ).hexdigest()
            payload = {
                "tenant_id": str(tenant_id.value),
                "aoi_id": str(command.aoi_id) if command.aoi_id else None,
                "year": command.year,
                "week": command.week,
            }

            job_id = await self.job_repo.create_job(
                tenant_id=tenant_id,
                aoi_id=command.aoi_id,
                job_type=job_type,
                job_key=job_key,
                payload_json=json.dumps(payload),
            )

            await self.queue.publish(
                self.queue_name,
                {
                    "job_id": str(job_id),
                    "job_type": job_type,
                    "payload": payload,
                },
            )

            results.append({"job_type": job_type, "job_id": str(job_id)})

        return {"queued": len(results), "jobs": results}
