"""Job DTOs for application layer."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId


class ListJobsCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: Optional[UUID] = None
    job_type: Optional[str] = None
    status: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=100)


class GetJobCommand(ImmutableDTO):
    tenant_id: TenantId
    job_id: UUID


class ListJobRunsCommand(ImmutableDTO):
    tenant_id: TenantId
    job_id: UUID
    limit: int = Field(default=10, ge=1, le=100)


class RetryJobCommand(ImmutableDTO):
    tenant_id: TenantId
    job_id: UUID


class CancelJobCommand(ImmutableDTO):
    tenant_id: TenantId
    job_id: UUID


class JobResult(ImmutableDTO):
    id: UUID
    aoi_id: Optional[UUID] = None
    job_type: str
    status: str
    payload: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class JobRunResult(ImmutableDTO):
    id: UUID
    job_id: UUID
    attempt: int
    status: str
    metrics: Optional[dict] = None
    error: Optional[dict] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
