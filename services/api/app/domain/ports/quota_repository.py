"""Port for quota data access."""
from __future__ import annotations

from datetime import date
from typing import Protocol


class IQuotaRepository(Protocol):
    """Quota data access port."""

    def get_tenant_tier(self, tenant_id: str) -> str:
        """Get tenant tier (PERSONAL, COMPANY_BASIC, etc.)."""
        ...

    def count_aois(self, tenant_id: str) -> int:
        """Count active AOIs for tenant."""
        ...

    def count_farms(self, tenant_id: str) -> int:
        """Count farms for tenant."""
        ...

    def count_backfills_on_date(self, tenant_id: str, on_date: date) -> int:
        """Count backfill jobs created on a specific date."""
        ...

    def count_members(self, tenant_id: str) -> int:
        """Count active members for tenant."""
        ...

    def count_ai_threads_on_date(self, tenant_id: str, on_date: date) -> int:
        """Count AI assistant threads created on a specific date."""
        ...
