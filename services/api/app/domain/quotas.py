"""
Quota enforcement system for multi-tenant platform.
Implements tier-based limits for PERSONAL, COMPANY_BASIC, COMPANY_PRO, and ENTERPRISE.
"""
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import structlog

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
    }
}


class QuotaExceededError(Exception):
    """Raised when a quota limit is exceeded"""
    def __init__(self, quota_type: str, limit: int, current: int):
        self.quota_type = quota_type
        self.limit = limit
        self.current = current
        super().__init__(f"Quota exceeded for {quota_type}: {current}/{limit}")


def get_tenant_tier(tenant_id: str, db: Session) -> str:
    """
    Get tenant tier definitions.
    Derived from tenant.type and tenant.plan.
    """
    sql = text("""
        SELECT type, plan FROM tenants 
        WHERE id = :tenant_id
    """)
    
    result = db.execute(sql, {"tenant_id": tenant_id}).fetchone()
    
    if not result:
        # Default to PERSONAL for safety
        return "PERSONAL"
    
    # If PERSONAL type, return PERSONAL tier
    if result.type == "PERSONAL":
        return "PERSONAL"
        
    # Combine TYPE_PLAN (e.g., COMPANY_BASIC, COMPANY_PRO)
    # Ensure uppercase to match QUOTAS keys
    tier = f"{result.type}_{result.plan}".upper()
    
    # Fallback if specific combination doesn't exist in QUOTAS
    if tier not in QUOTAS:
        logger.warning("unknown_tier_key", tier=tier, tenant_id=tenant_id)
        return "COMPANY_BASIC" # Fallback
        
    return tier


def get_quota_limits(tenant_id: str, db: Session) -> Dict[str, Any]:
    """Get quota limits for a tenant"""
    tier = get_tenant_tier(tenant_id, db)
    return QUOTAS.get(tier, QUOTAS["PERSONAL"])


def check_aoi_quota(tenant_id: str, db: Session) -> None:
    """Check if tenant can create more AOIs"""
    limits = get_quota_limits(tenant_id, db)
    max_aois = limits["max_aois"]
    
    if max_aois == -1:  # Unlimited
        return
    
    # Count current AOIs
    sql = text("""
        SELECT COUNT(*) as count
        FROM aois
        WHERE tenant_id = :tenant_id AND status = 'ACTIVE'
    """)
    
    result = db.execute(sql, {"tenant_id": tenant_id}).fetchone()
    current_count = result.count if result else 0
    
    if current_count >= max_aois:
        logger.warning("aoi_quota_exceeded", tenant_id=tenant_id, current=current_count, limit=max_aois)
        raise QuotaExceededError("max_aois", max_aois, current_count)
    
    logger.info("aoi_quota_check_passed", tenant_id=tenant_id, current=current_count, limit=max_aois)


def check_farm_quota(tenant_id: str, db: Session) -> None:
    """Check if tenant can create more farms"""
    limits = get_quota_limits(tenant_id, db)
    max_farms = limits["max_farms"]
    
    if max_farms == -1:  # Unlimited
        return
    
    # Count current farms
    sql = text("""
        SELECT COUNT(*) as count
        FROM farms
        WHERE tenant_id = :tenant_id
    """)
    
    result = db.execute(sql, {"tenant_id": tenant_id}).fetchone()
    current_count = result.count if result else 0
    
    if current_count >= max_farms:
        logger.warning("farm_quota_exceeded", tenant_id=tenant_id, current=current_count, limit=max_farms)
        raise QuotaExceededError("max_farms", max_farms, current_count)


def check_backfill_quota(tenant_id: str, weeks_count: int, db: Session) -> None:
    """Check if tenant can perform backfill"""
    limits = get_quota_limits(tenant_id, db)
    max_weeks = limits["max_backfill_weeks"]
    max_per_day = limits["backfills_per_day"]
    
    # Check weeks limit
    if max_weeks != -1 and weeks_count > max_weeks:
        logger.warning("backfill_weeks_exceeded", tenant_id=tenant_id, requested=weeks_count, limit=max_weeks)
        raise QuotaExceededError("max_backfill_weeks", max_weeks, weeks_count)
    
    # Check daily limit
    if max_per_day != -1:
        today = datetime.utcnow().date()
        sql = text("""
            SELECT COUNT(*) as count
            FROM jobs
            WHERE tenant_id = :tenant_id 
              AND job_type = 'BACKFILL'
              AND DATE(created_at) = :today
        """)
        
        result = db.execute(sql, {"tenant_id": tenant_id, "today": today}).fetchone()
        current_count = result.count if result else 0
        
        if current_count >= max_per_day:
            logger.warning("backfill_daily_quota_exceeded", tenant_id=tenant_id, current=current_count, limit=max_per_day)
            raise QuotaExceededError("backfills_per_day", max_per_day, current_count)


def check_member_quota(tenant_id: str, db: Session) -> None:
    """Check if tenant can invite more members"""
    limits = get_quota_limits(tenant_id, db)
    max_members = limits["max_members"]
    
    if max_members == -1:  # Unlimited
        return
    
    # Count current active members
    sql = text("""
        SELECT COUNT(*) as count
        FROM memberships
        WHERE tenant_id = :tenant_id AND status = 'ACTIVE'
    """)
    
    result = db.execute(sql, {"tenant_id": tenant_id}).fetchone()
    current_count = result.count if result else 0
    
    if current_count >= max_members:
        logger.warning("member_quota_exceeded", tenant_id=tenant_id, current=current_count, limit=max_members)
        raise QuotaExceededError("max_members", max_members, current_count)


def check_ai_assistant_quota(tenant_id: str, db: Session) -> None:
    """Check if tenant can create more AI assistant threads today"""
    limits = get_quota_limits(tenant_id, db)
    
    if not limits["ai_assistant_enabled"]:
        raise QuotaExceededError("ai_assistant_enabled", 0, 0)
    
    max_per_day = limits["ai_assistant_threads_per_day"]
    
    if max_per_day == -1:  # Unlimited
        return
    
    # Count threads created today
    today = datetime.utcnow().date()
    sql = text("""
        SELECT COUNT(*) as count
        FROM ai_assistant_threads
        WHERE tenant_id = :tenant_id 
          AND DATE(created_at) = :today
    """)
    
    result = db.execute(sql, {"tenant_id": tenant_id, "today": today}).fetchone()
    current_count = result.count if result else 0
    
    if current_count >= max_per_day:
        logger.warning("ai_assistant_quota_exceeded", tenant_id=tenant_id, current=current_count, limit=max_per_day)
        raise QuotaExceededError("ai_assistant_threads_per_day", max_per_day, current_count)


def check_signals_enabled(tenant_id: str, db: Session) -> None:
    """Check if signals are enabled for tenant"""
    limits = get_quota_limits(tenant_id, db)
    
    if not limits["signals_enabled"]:
        raise QuotaExceededError("signals_enabled", 0, 0)
