"""
Comprehensive audit logging system.
Logs all sensitive operations to audit_log table for compliance and security.
"""
from __future__ import annotations

from typing import Dict, Any, Optional

import structlog

from app.domain.ports.audit_repository import IAuditRepository

logger = structlog.get_logger()


class AuditLogger:
    """Centralized audit logging."""

    def __init__(self, audit_repo: IAuditRepository):
        self.audit_repo = audit_repo

    def log(
        self,
        tenant_id: str,
        actor_membership_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log an audit event.

        Args:
            tenant_id: Tenant performing the action
            actor_membership_id: Membership ID of the actor (None for system actions)
            action: Action performed (e.g., "CREATE", "UPDATE", "DELETE", "INVITE", "APPROVE")
            resource_type: Type of resource (e.g., "membership", "aoi", "signal", "approval")
            resource_id: ID of the resource
            changes: Dict of changes (before/after values)
            metadata: Additional context
        """
        actor_type = "MEMBERSHIP" if actor_membership_id else "SYSTEM"

        try:
            event = {
                "tenant_id": tenant_id,
                "actor_id": actor_membership_id,
                "actor_type": actor_type,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "changes": changes,
                "metadata": metadata,
            }
            self.audit_repo.save_event(event)

            logger.info(
                "audit_logged",
                tenant_id=tenant_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
            )
        except Exception as e:
            logger.error("audit_log_failed", exc_info=e)
            # Don't fail the main operation if audit fails

    # Convenience methods for common audit events

    def log_membership_invite(self, tenant_id: str, actor_id: str, invited_email: str, role: str):
        """Log membership invitation"""
        self.log(
            tenant_id=tenant_id,
            actor_membership_id=actor_id,
            action="INVITE_MEMBER",
            resource_type="membership",
            resource_id=None,
            metadata={"invited_email": invited_email, "role": role},
        )

    def log_membership_role_change(self, tenant_id: str, actor_id: str, membership_id: str, old_role: str, new_role: str):
        """Log role change"""
        self.log(
            tenant_id=tenant_id,
            actor_membership_id=actor_id,
            action="UPDATE_ROLE",
            resource_type="membership",
            resource_id=membership_id,
            changes={"role": {"before": old_role, "after": new_role}},
        )

    def log_membership_status_change(self, tenant_id: str, actor_id: str, membership_id: str, old_status: str, new_status: str):
        """Log status change"""
        self.log(
            tenant_id=tenant_id,
            actor_membership_id=actor_id,
            action="UPDATE_STATUS",
            resource_type="membership",
            resource_id=membership_id,
            changes={"status": {"before": old_status, "after": new_status}},
        )

    def log_tenant_settings_change(self, tenant_id: str, actor_id: str, changes: Dict[str, Any]):
        """Log tenant settings update"""
        self.log(
            tenant_id=tenant_id,
            actor_membership_id=actor_id,
            action="UPDATE_SETTINGS",
            resource_type="tenant_settings",
            resource_id=tenant_id,
            changes=changes,
        )

    def log_signal_action(self, tenant_id: str, actor_id: str, signal_id: str, action: str):
        """Log signal action (ACK, RESOLVE, DISMISS)"""
        self.log(
            tenant_id=tenant_id,
            actor_membership_id=actor_id,
            action=f"SIGNAL_{action}",
            resource_type="opportunity_signal",
            resource_id=signal_id,
        )

    def log_signal_feedback(self, tenant_id: str, actor_id: str, signal_id: str, label: str, note: Optional[str]):
        """Log signal feedback"""
        self.log(
            tenant_id=tenant_id,
            actor_membership_id=actor_id,
            action="SIGNAL_FEEDBACK",
            resource_type="opportunity_signal",
            resource_id=signal_id,
            metadata={"label": label, "note": note},
        )

    def log_alert_action(self, tenant_id: str, actor_id: str, alert_id: str, action: str):
        """Log alert action (ACK, RESOLVE, DISMISS)"""
        self.log(
            tenant_id=tenant_id,
            actor_membership_id=actor_id,
            action=f"ALERT_{action}",
            resource_type="alert",
            resource_id=alert_id,
        )

    def log_hil_decision(self, tenant_id: str, actor_id: str, approval_id: str, decision: str, tool_name: str, note: Optional[str]):
        """Log Human-in-the-Loop approval decision"""
        self.log(
            tenant_id=tenant_id,
            actor_membership_id=actor_id,
            action=f"HIL_{decision}",
            resource_type="ai_assistant_approval",
            resource_id=approval_id,
            metadata={"tool_name": tool_name, "note": note},
        )

    def log_job_action(self, tenant_id: str, actor_id: Optional[str], job_id: str, action: str):
        """Log job action (RETRY, CANCEL)"""
        self.log(
            tenant_id=tenant_id,
            actor_membership_id=actor_id,
            action=f"JOB_{action}",
            resource_type="job",
            resource_id=job_id,
        )

    def log_dlq_action(self, actor_id: str, action: str, message_count: int, reason: Optional[str]):
        """Log DLQ action (REDRIVE, PURGE)"""
        self.log(
            tenant_id="SYSTEM",
            actor_membership_id=actor_id,
            action=f"DLQ_{action}",
            resource_type="dlq",
            resource_id=None,
            metadata={"message_count": message_count, "reason": reason},
        )

    def log_backfill_request(self, tenant_id: str, actor_id: str, aoi_id: str, from_date: str, to_date: str, weeks_count: int):
        """Log backfill request"""
        self.log(
            tenant_id=tenant_id,
            actor_membership_id=actor_id,
            action="BACKFILL_REQUEST",
            resource_type="aoi",
            resource_id=aoi_id,
            metadata={"from_date": from_date, "to_date": to_date, "weeks_count": weeks_count},
        )

    def log_export_request(self, tenant_id: str, actor_id: str, export_format: str, filters: Optional[Dict]):
        """Log data export request"""
        self.log(
            tenant_id=tenant_id,
            actor_membership_id=actor_id,
            action="EXPORT_DATA",
            resource_type="export",
            resource_id=None,
            metadata={"format": export_format, "filters": filters},
        )


def get_audit_logger(audit_repo: IAuditRepository) -> AuditLogger:
    """Factory function to get audit logger"""
    return AuditLogger(audit_repo)
