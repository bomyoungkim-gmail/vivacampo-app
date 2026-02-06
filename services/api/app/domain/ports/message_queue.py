"""Message queue port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class Message:
    id: str
    body: dict
    attributes: Optional[dict] = None


class IMessageQueue(ABC):
    @abstractmethod
    async def publish(self, queue_name: str, message: dict, delay_seconds: int = 0) -> str:
        """Publish a message to the queue."""
        raise NotImplementedError

    @abstractmethod
    async def consume(
        self,
        queue_name: str,
        handler: Callable[[Message], None],
        max_messages: int = 10,
        wait_time_seconds: int = 20,
    ) -> None:
        """Consume messages from the queue."""
        raise NotImplementedError
