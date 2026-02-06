"""System admin DTOs."""
from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.domain.base import ImmutableDTO


class ListTenantsCommand(ImmutableDTO):
    tenant_type: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=100)


class CreateTenantCommand(ImmutableDTO):
    name: str
    tenant_type: str


class UpdateTenantCommand(ImmutableDTO):
    tenant_id: UUID
    status: str


class ListSystemJobsCommand(ImmutableDTO):
    status: Optional[str] = None
    job_type: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=200)


class RetryJobCommand(ImmutableDTO):
    job_id: UUID


class ReprocessMissingAoisCommand(ImmutableDTO):
    days: int = Field(default=56, ge=1, le=365)
    limit: int = Field(default=200, ge=1, le=500)


class ListMissingWeeksCommand(ImmutableDTO):
    weeks: int = Field(default=12, ge=1, le=104)
    limit: int = Field(default=50, ge=1, le=200)


class ReprocessMissingWeeksCommand(ImmutableDTO):
    weeks: int = Field(default=12, ge=1, le=104)
    limit: int = Field(default=50, ge=1, le=200)
    max_runs_per_aoi: int = Field(default=3, ge=1, le=6)


class GlobalAuditLogCommand(ImmutableDTO):
    limit: int = Field(default=100, ge=1, le=200)
