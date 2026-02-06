"""Job use cases using ports and DTOs."""
from __future__ import annotations

from typing import List

from app.application.dtos.jobs import (
    CancelJobCommand,
    GetJobCommand,
    JobResult,
    JobRunResult,
    ListJobRunsCommand,
    ListJobsCommand,
    RetryJobCommand,
)
from app.domain.ports.job_repository import IJobRepository


class ListJobsUseCase:
    def __init__(self, repo: IJobRepository):
        self.repo = repo

    async def execute(self, command: ListJobsCommand) -> List[JobResult]:
        rows = await self.repo.list_jobs(
            tenant_id=command.tenant_id,
            aoi_id=command.aoi_id,
            job_type=command.job_type,
            status=command.status,
            limit=command.limit,
        )
        return [JobResult(**row) for row in rows]


class GetJobUseCase:
    def __init__(self, repo: IJobRepository):
        self.repo = repo

    async def execute(self, command: GetJobCommand) -> JobResult | None:
        row = await self.repo.get_job(command.tenant_id, command.job_id)
        return JobResult(**row) if row else None


class ListJobRunsUseCase:
    def __init__(self, repo: IJobRepository):
        self.repo = repo

    async def execute(self, command: ListJobRunsCommand) -> tuple[list[JobRunResult], bool]:
        rows, job_exists = await self.repo.list_runs(command.tenant_id, command.job_id, command.limit)
        return [JobRunResult(**row) for row in rows], job_exists


class RetryJobUseCase:
    def __init__(self, repo: IJobRepository):
        self.repo = repo

    async def execute(self, command: RetryJobCommand) -> bool:
        job = await self.repo.get_job(command.tenant_id, command.job_id)
        if not job:
            return False
        if job["status"] not in ["FAILED", "CANCELLED"]:
            raise ValueError(f"Cannot retry job in {job['status']} state")
        return await self.repo.update_status(command.tenant_id, command.job_id, "PENDING")


class CancelJobUseCase:
    def __init__(self, repo: IJobRepository):
        self.repo = repo

    async def execute(self, command: CancelJobCommand) -> bool:
        job = await self.repo.get_job(command.tenant_id, command.job_id)
        if not job:
            return False
        if job["status"] not in ["PENDING", "RUNNING"]:
            raise ValueError(f"Cannot cancel job in {job['status']} state")
        return await self.repo.update_status(command.tenant_id, command.job_id, "CANCELLED")
