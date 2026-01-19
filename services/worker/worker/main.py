import asyncio
import json
import hashlib
from datetime import datetime
from uuid import UUID
import structlog
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session
from worker.database import get_db
from worker.shared.aws_clients import SQSClient
from worker.jobs.process_week import process_week_handler
from worker.jobs.alerts_week import handle_alerts_week
from worker.jobs.signals_week import signals_week_handler
from worker.jobs.forecast_week import handle_forecast_week
from worker.jobs.backfill import handle_backfill
from worker.jobs.process_radar import process_radar_week_handler
from worker.jobs.process_topography import process_topography_handler
from worker.jobs.process_weather import process_weather_history_handler as process_weather_handler

logger = structlog.get_logger()

# Job type to handler mapping
JOB_HANDLERS = {
    "PROCESS_WEEK": process_week_handler,
    "PROCESS_RADAR_WEEK": process_radar_week_handler,
    "PROCESS_TOPOGRAPHY": process_topography_handler,
    "PROCESS_WEATHER": process_weather_handler,
    "ALERTS_WEEK": handle_alerts_week,
    "SIGNALS_WEEK": signals_week_handler,
    "FORECAST_WEEK": handle_forecast_week,
    "BACKFILL": handle_backfill,
}


def run_handler(handler, job_id: str, payload: dict, db: Session):
    """
    Run sync or async job handlers with a consistent wrapper.
    """
    if asyncio.iscoroutinefunction(handler):
        job = {
            "id": job_id,
            "tenant_id": payload.get("tenant_id"),
            "aoi_id": payload.get("aoi_id"),
            "payload": payload,
        }
        return asyncio.run(handler(job, db))

    return handler(job_id=job_id, payload=payload, db=db)


def calculate_job_key(tenant_id: str, aoi_id: str, year: int, week: int, job_type: str, pipeline_version: str) -> str:
    """
    Calculate idempotent job key.
    job_key = sha256(tenant_id+aoi_id+year+week+job_type+pipeline_version)
    """
    data = f"{tenant_id}{aoi_id}{year}{week}{job_type}{pipeline_version}"
    return hashlib.sha256(data.encode()).hexdigest()


def process_message(message: dict, db: Session):
    """
    Process a single SQS message.
    """
    try:
        # Parse message body
        body = json.loads(message['Body'])
        
        job_id = body.get('job_id')
        job_type = body.get('job_type')
        payload = body.get('payload', {})
        
        logger.info("processing_job", job_id=job_id, job_type=job_type)
        
        # Get handler
        handler = JOB_HANDLERS.get(job_type)
        if not handler:
            logger.error("unknown_job_type", job_type=job_type)
            return
        
        # Execute handler
        run_handler(handler, job_id, payload, db)
        
        logger.info("job_completed", job_id=job_id, job_type=job_type)
        
    except Exception as e:
        logger.error("job_failed", exc_info=e, message_id=message.get('MessageId'))
        raise


def main():
    """
    Main worker loop.
    Polls SQS queue and processes jobs.
    """
    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )
    
    logger.info("worker_starting")
    
    # Initialize SQS client
    sqs = SQSClient()
    
    # Main loop
    while True:
        try:
            # 1. Try High Priority Queue first (Short poll)
            # Use short wait time to avoid blocking too long if empty, 
            # but long enough to catch messages if bursty.
            high_messages = sqs.receive_messages(
                queue_url=sqs.queue_high_url, 
                max_messages=1, 
                wait_time=2
            )
            
            if high_messages:
                messages = high_messages
                logger.info("processing_high_priority_job")
            else:
                # 2. If no high priority, check Default Queue (Long polling)
                # Only check default if high is empty
                messages = sqs.receive_messages(
                    queue_url=sqs.queue_url, 
                    max_messages=1, 
                    wait_time=20
                )
            
            if not messages:
                continue
            
            for message in messages:
                db = get_db()
                try:
                    # Process message
                    process_message(message, db)
                    
                    # Delete message from its source queue
                    # We need to know which queue it came from to delete it correctly
                    # SQSClient.delete_message now accepts queue_url
                    source_queue = sqs.queue_high_url if high_messages else sqs.queue_url
                    sqs.delete_message(message['ReceiptHandle'], queue_url=source_queue)
                    
                except Exception as e:
                    logger.error("message_processing_failed", exc_info=e)
                    # Message will return to queue after visibility timeout
                finally:
                    db.close()
        
        except KeyboardInterrupt:
            logger.info("worker_shutdown")
            break
        except Exception as e:
            logger.error("worker_error", exc_info=e)
            import time
            time.sleep(1) # Prevent tight loop on error


if __name__ == "__main__":
    main()
