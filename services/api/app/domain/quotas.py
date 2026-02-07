"""
Quota enforcement system for multi-tenant platform.
Implements tier-based limits for PERSONAL, COMPANY_BASIC, COMPANY_PRO, and ENTERPRISE.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

import structlog

from app.domain.ports.quota_repository import IQuotaRepository

logger = structlog.get_logger()

# Quota definitions by tenant tier
QUOTAS = {
    "PERSONAL": {
        "max_aois": 3,
        "max_backfill_weeks": 52,
        "backfills_per_day": 2,
        "max_farms": 2,
        "max_members": 1,  # Only owner
        "signals_enabled": True,
        "ai_assistant_enabled": True,
        "ai_assistant_threads_per_day": 5,
    },
    "COMPANY_BASIC": {
        "max_aois": 20,
        "max_backfill_weeks": 104,
        "backfills_per_day": 10,
        "max_farms": 10,
        "max_members": 5,
        "signals_enabled": True,
        "ai_assistant_enabled": True,
        "ai_assistant_threads_per_day": 50,
    },
    "COMPANY_PRO": {
        "max_aois": 100,
        "max_backfill_weeks": 260,
        "backfills_per_day": 50,
        "max_farms": 50,
        "max_members": 25,
        "signals_enabled": True,
        "ai_assistant_enabled": True,
        "ai_assistant_threads_per_day": 200,
    },
    "ENTERPRISE": {
        "max_aois": -1,  # Unlimited
        "max_backfill_weeks": -1,
        "backfills_per_day": -1,
        "max_farms": -1,
        "max_members": -1,
        "signals_enabled": True,
        "ai_assistant_enabled": True,
        "ai_assistant_threads_per_day": -1,
    },
}


class QuotaExceededError(Exception):
    """Raised when a quota limit is exceeded"""

    def __init__(self, quota_type: str, limit: int, current: int):
        self.quota_type = quota_type
        self.limit = limit
        self.current = current
        super().__init__(f"Quota exceeded for {quota_type}: {current}/{limit}")


class QuotaService:
    """Quota enforcement service (domain logic)."""

    def __init__(self, quota_repo: IQuotaRepository):
        self.quota_repo = quota_repo

    def get_quota_limits(self, tenant_id: str) -> Dict[str, Any]:
        tier = self.quota_repo.get_tenant_tier(tenant_id)
        if tier not in QUOTAS:
            logger.warning("unknown_tier_key", tier=tier, tenant_id=tenant_id)
            tier = "COMPANY_BASIC"
        return QUOTAS.get(tier, QUOTAS["PERSONAL"])

    def check_aoi_quota(self, tenant_id: str) -> None:
        """Check if tenant can create more AOIs"""
        limits = self.get_quota_limits(tenant_id)
        max_aois = limits["max_aois"]

        if max_aois == -1:  # Unlimited
            return

        current_count = self.quota_repo.count_aois(tenant_id)

        if current_count >= max_aois:
            logger.warning(
                "aoi_quota_exceeded",
                tenant_id=tenant_id,
                current=current_count,
                limit=max_aois,
            )
            raise QuotaExceededError("max_aois", max_aois, current_count)

        logger.info(
            "aoi_quota_check_passed",
            tenant_id=tenant_id,
            current=current_count,
            limit=max_aois,
        )

    def check_farm_quota(self, tenant_id: str) -> None:
        """Check if tenant can create more farms"""
        limits = self.get_quota_limits(tenant_id)
        max_farms = limits["max_farms"]

        if max_farms == -1:  # Unlimited
            return

        current_count = self.quota_repo.count_farms(tenant_id)

        if current_count >= max_farms:
            logger.warning(
                "farm_quota_exceeded",
                tenant_id=tenant_id,
                current=current_count,
                limit=max_farms,
            )
            raise QuotaExceededError("max_farms", max_farms, current_count)

    def check_backfill_quota(self, tenant_id: str, weeks_count: int) -> None:
        """Check if tenant can perform backfill"""
        limits = self.get_quota_limits(tenant_id)
        max_weeks = limits["max_backfill_weeks"]
        max_per_day = limits["backfills_per_day"]

        if max_weeks != -1 and weeks_count > max_weeks:
            logger.warning(
                "backfill_weeks_exceeded",
                tenant_id=tenant_id,
                requested=weeks_count,
                limit=max_weeks,
            )
            raise QuotaExceededError("max_backfill_weeks", max_weeks, weeks_count)

        if max_per_day != -1:
            today = datetime.now(timezone.utc).date()
            current_count = self.quota_repo.count_backfills_on_date(tenant_id, today)

            if current_count >= max_per_day:
                logger.warning(
                    "backfill_daily_quota_exceeded",
                    tenant_id=tenant_id,
                    current=current_count,
                    limit=max_per_day,
                )
                raise QuotaExceededError("backfills_per_day", max_per_day, current_count)

    def check_member_quota(self, tenant_id: str) -> None:
        """Check if tenant can invite more members"""
        limits = self.get_quota_limits(tenant_id)
        max_members = limits["max_members"]

        if max_members == -1:  # Unlimited
            return

        current_count = self.quota_repo.count_members(tenant_id)

        if current_count >= max_members:
            logger.warning(
                "member_quota_exceeded",
                tenant_id=tenant_id,
                current=current_count,
                limit=max_members,
            )
            raise QuotaExceededError("max_members", max_members, current_count)

    def check_ai_assistant_quota(self, tenant_id: str) -> None:
        """Check if tenant can create more AI assistant threads today"""
        limits = self.get_quota_limits(tenant_id)

        if not limits["ai_assistant_enabled"]:
            raise QuotaExceededError("ai_assistant_enabled", 0, 0)

        max_per_day = limits["ai_assistant_threads_per_day"]

        if max_per_day == -1:  # Unlimited
            return

        today = datetime.now(timezone.utc).date()
        current_count = self.quota_repo.count_ai_threads_on_date(tenant_id, today)

        if current_count >= max_per_day:
            logger.warning(
                "ai_assistant_quota_exceeded",
                tenant_id=tenant_id,
                current=current_count,
                limit=max_per_day,
            )
            raise QuotaExceededError("ai_assistant_threads_per_day", max_per_day, current_count)

    def check_signals_enabled(self, tenant_id: str) -> None:
        """Check if signals are enabled for tenant"""
        limits = self.get_quota_limits(tenant_id)

        if not limits["signals_enabled"]:
            raise QuotaExceededError("signals_enabled", 0, 0)
