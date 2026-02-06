"""SQS adapter implementing IMessageQueue with retry/backoff."""
import json
from typing import Callable, Optional

import structlog

from app.config import settings
from app.domain.ports.message_queue import IMessageQueue, Message
from app.infrastructure.resilience import retry_with_backoff, circuit
from app.infrastructure.sqs_client import SQSClientWrapper

logger = structlog.get_logger()


class SQSAdapter(IMessageQueue):
    """AWS SQS implementation with retry and basic URL caching."""

    def __init__(self, client: Optional[SQSClientWrapper] = None):
        self.client = client or SQSClientWrapper()
        self._queue_urls: dict[str, str] = {}

    def _resolve_queue_url(self, queue_name_or_url: str) -> str:
        if queue_name_or_url.startswith("http"):
            return queue_name_or_url

        if queue_name_or_url in self._queue_urls:
            return self._queue_urls[queue_name_or_url]

        try:
            response = self.client.client.get_queue_url(QueueName=queue_name_or_url)
            queue_url = response["QueueUrl"]
        except Exception as exc:
            logger.warning("sqs_queue_resolution_failed", queue=queue_name_or_url, exc_info=exc)
            if settings.aws_endpoint_url:
                queue_url = f"{settings.aws_endpoint_url}/queue/{queue_name_or_url}"
            else:
                queue_url = queue_name_or_url

        self._queue_urls[queue_name_or_url] = queue_url
        return queue_url

    @retry_with_backoff(max_attempts=3, initial_delay=1.0, max_delay=8.0)
    @circuit(failure_threshold=3, recovery_timeout=120)
    async def publish(self, queue_name: str, message: dict, delay_seconds: int = 0) -> str:
        queue_url = self._resolve_queue_url(queue_name)
        response = self.client.client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message, default=str),
            DelaySeconds=delay_seconds,
        )
        message_id = response["MessageId"]
        logger.info("sqs_message_published", queue=queue_name, message_id=message_id)
        return message_id

    async def consume(
        self,
        queue_name: str,
        handler: Callable[[Message], None],
        max_messages: int = 10,
        wait_time_seconds: int = 20,
    ) -> None:
        queue_url = self._resolve_queue_url(queue_name)
        response = self.client.client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time_seconds,
        )

        for msg in response.get("Messages", []):
            try:
                body = json.loads(msg["Body"])
                message = Message(
                    id=msg["MessageId"],
                    body=body,
                    attributes=msg.get("Attributes", {}),
                )
                await handler(message)
                self.client.client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=msg["ReceiptHandle"],
                )
            except Exception as exc:
                logger.error("sqs_message_processing_failed", exc_info=exc)
                # Message returns to queue after visibility timeout
