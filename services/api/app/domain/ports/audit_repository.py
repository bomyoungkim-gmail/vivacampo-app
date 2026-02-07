"""Port for audit log persistence."""
from __future__ import annotations

from typing import Protocol, Dict, Any


class IAuditRepository(Protocol):
    """Audit log persistence port."""

    def save_event(self, event: Dict[str, Any]) -> None:
        """Persist audit event."""
        ...
