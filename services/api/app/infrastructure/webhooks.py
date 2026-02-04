"""
Webhook execution logic.
Processes outbox events and sends webhooks to tenant endpoints.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
import structlog
import httpx
from typing import Dict, Any
import json
from datetime import datetime, timezone

logger = structlog.get_logger()


async def execute_webhook(
    tenant_id: str,
    event_type: str,
    payload: Dict[str, Any],
    db: Session
):
    """
    Execute webhook for a tenant event.
    
    Args:
        tenant_id: Tenant ID
        event_type: Event type (e.g., "signal.created", "alert.triggered")
        payload: Event payload
        db: Database session
    """
    # Get active webhooks for this tenant and event type
    sql = text("""
        SELECT id, url, secret, events
        FROM tenant_webhooks
        WHERE tenant_id = :tenant_id AND status = 'ACTIVE'
    """)
    
    result = db.execute(sql, {"tenant_id": tenant_id})
    webhooks = result.fetchall()
    
    for webhook in webhooks:
        # Check if webhook is subscribed to this event type
        if webhook.events is None:
            subscribed_events = []
        elif isinstance(webhook.events, (list, tuple)):
            subscribed_events = list(webhook.events)
        else:
            subscribed_events = json.loads(webhook.events)
        if event_type not in subscribed_events:
            continue
        
        # Create outbox entry
        sql = text("""
            INSERT INTO tenant_event_outbox
            (tenant_id, webhook_id, event_type, payload, status)
            VALUES (:tenant_id, :webhook_id, :event_type, :payload, 'PENDING')
            RETURNING id
        """)
        
        result = db.execute(sql, {
            "tenant_id": tenant_id,
            "webhook_id": str(webhook.id),
            "event_type": event_type,
            "payload": json.dumps(payload)
        })
        db.commit()
        
        outbox_id = result.fetchone()[0]
        
        # Send webhook asynchronously
        await send_webhook_async(
            outbox_id=str(outbox_id),
            url=webhook.url,
            secret=webhook.secret,
            event_type=event_type,
            payload=payload,
            db=db
        )


async def send_webhook_async(
    outbox_id: str,
    url: str,
    secret: str,
    event_type: str,
    payload: Dict[str, Any],
    db: Session
):
    """
    Send webhook HTTP request.
    
    Args:
        outbox_id: Outbox entry ID
        url: Webhook URL
        secret: Webhook secret for HMAC signature
        event_type: Event type
        payload: Event payload
        db: Database session
    """
    try:
        # Generate HMAC signature
        import hmac
        import hashlib
        
        payload_json = json.dumps(payload)
        signature = hmac.new(
            secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Send HTTP POST
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json={
                    "event_type": event_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": payload
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": f"sha256={signature}",
                    "X-Event-Type": event_type
                }
            )
            
            response.raise_for_status()
        
        # Mark as delivered
        sql = text("""
            UPDATE tenant_event_outbox
            SET status = 'DELIVERED',
                delivered_at = now(),
                http_status = :status
            WHERE id = :outbox_id
        """)
        
        db.execute(sql, {
            "status": response.status_code,
            "outbox_id": outbox_id
        })
        db.commit()
        
        logger.info("webhook_delivered",
                   outbox_id=outbox_id,
                   url=url,
                   status=response.status_code)
    
    except Exception as e:
        # Mark as failed
        sql = text("""
            UPDATE tenant_event_outbox
            SET status = 'FAILED',
                error_message = :error,
                retry_count = retry_count + 1
            WHERE id = :outbox_id
        """)
        
        db.execute(sql, {
            "error": str(e),
            "outbox_id": outbox_id
        })
        db.commit()
        
        logger.error("webhook_failed",
                    outbox_id=outbox_id,
                    url=url,
                    exc_info=e)


async def process_outbox_worker(db: Session):
    """
    Background worker to process pending webhook outbox entries.
    Should be run periodically (e.g., every minute).
    """
    # Get pending entries
    sql = text("""
        SELECT id, tenant_id, webhook_id, event_type, payload
        FROM tenant_event_outbox
        WHERE status = 'PENDING'
          AND retry_count < 3
          AND created_at > now() - interval '24 hours'
        ORDER BY created_at ASC
        LIMIT 100
    """)
    
    result = db.execute(sql)
    entries = result.fetchall()
    
    logger.info("processing_outbox", count=len(entries))
    
    for entry in entries:
        # Get webhook details
        sql = text("""
            SELECT url, secret
            FROM tenant_webhooks
            WHERE id = :webhook_id AND status = 'ACTIVE'
        """)
        
        webhook = db.execute(sql, {"webhook_id": entry.webhook_id}).fetchone()
        
        if not webhook:
            # Webhook deleted or inactive, mark as failed
            sql = text("""
                UPDATE tenant_event_outbox
                SET status = 'FAILED', error_message = 'Webhook inactive or deleted'
                WHERE id = :outbox_id
            """)
            db.execute(sql, {"outbox_id": str(entry.id)})
            db.commit()
            continue
        
        # Send webhook
        await send_webhook_async(
            outbox_id=str(entry.id),
            url=webhook.url,
            secret=webhook.secret,
            event_type=entry.event_type,
            payload=json.loads(entry.payload),
            db=db
        )
