"""Ports for worker job scheduling and persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class JobRepository(ABC):
    """Persist and update job metadata."""

    @abstractmethod
    def mark_status(self, job_id: str, status: str, error_message: Optional[str] = None) -> None:
        """Update job status."""
        raise NotImplementedError

    @abstractmethod
    def upsert_job(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        job_type: str,
        job_key: str,
        payload: dict,
    ) -> Optional[str]:
        """Create or refresh a job and return the job id when enqueued."""
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        """Commit pending changes (if applicable)."""
        raise NotImplementedError


class SeasonRepository(ABC):
    """Access seasonal metadata for AOIs."""

    @abstractmethod
    def has_season(self, tenant_id: str, aoi_id: str) -> bool:
        """Return True if the AOI has a season configured."""
        raise NotImplementedError


class JobQueue(ABC):
    """Queue jobs for processing."""

    @abstractmethod
    def enqueue(self, *, job_id: str, job_type: str, payload: dict) -> None:
        """Send a job message to the queue."""
        raise NotImplementedError
