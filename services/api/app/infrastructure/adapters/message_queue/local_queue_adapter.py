"""In-memory message queue adapter for local/dev usage."""
from __future__ import annotations

import asyncio
from typing import Callable, Dict

import structlog

from app.domain.ports.message_queue import IMessageQueue, Message

logger = structlog.get_logger()


class LocalQueueAdapter(IMessageQueue):
    """Simple in-memory queue implementation."""

    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}

    def _get_queue(self, queue_name: str) -> asyncio.Queue:
        if queue_name not in self._queues:
            self._queues[queue_name] = asyncio.Queue()
        return self._queues[queue_name]

    async def publish(self, queue_name: str, message: dict, delay_seconds: int = 0) -> str:
        if delay_seconds:
            await asyncio.sleep(delay_seconds)
        queue = self._get_queue(queue_name)
        await queue.put(message)
        message_id = f"local-{queue_name}-{queue.qsize()}"
        logger.info("local_queue_published", queue=queue_name, message_id=message_id)
        return message_id

    async def consume(
        self,
        queue_name: str,
        handler: Callable[[Message], None],
        max_messages: int = 10,
        wait_time_seconds: int = 1,
    ) -> None:
        queue = self._get_queue(queue_name)
        count = 0

        while count < max_messages:
            try:
                body = await asyncio.wait_for(queue.get(), timeout=wait_time_seconds)
            except asyncio.TimeoutError:
                return

            message = Message(id=f"local-{queue_name}-{count}", body=body, attributes=None)
            await handler(message)
            count += 1
