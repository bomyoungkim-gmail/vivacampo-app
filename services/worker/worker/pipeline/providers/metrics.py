"""
Provider metrics (lightweight logging + optional Redis).
"""
from __future__ import annotations

from typing import Optional

import structlog

logger = structlog.get_logger()


class ProviderMetrics:
    """Record provider usage metrics (optional Redis)."""

    def __init__(self, redis_client: Optional[object] = None) -> None:
        self._redis = redis_client

    def record_call(
        self,
        provider_name: str,
        operation: str,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        logger.info(
            "provider_metric",
            provider=provider_name,
            operation=operation,
            duration_ms=round(duration_ms, 1),
            success=success,
            error=error,
        )

        if not self._redis:
            return

        try:
            key = f"provider_metrics:{provider_name}"
            pipe = self._redis.pipeline()
            pipe.hincrby(key, f"{operation}_total", 1)
            if not success:
                pipe.hincrby(key, f"{operation}_errors", 1)
            pipe.expire(key, 86400)
            pipe.execute()
        except Exception:
            pass
