import asyncio

from app.infrastructure.adapters.message_queue.local_queue_adapter import LocalQueueAdapter


def test_local_queue_publish_and_consume():
    adapter = LocalQueueAdapter()
    received = []

    async def handler(message):
        received.append(message.body)

    async def run():
        await adapter.publish("jobs", {"ok": True})
        await adapter.consume("jobs", handler, max_messages=1)

    asyncio.run(run())

    assert received == [{"ok": True}]
