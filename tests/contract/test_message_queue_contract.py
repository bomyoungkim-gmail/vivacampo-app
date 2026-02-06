import asyncio

from app.infrastructure.adapters.message_queue.local_queue_adapter import LocalQueueAdapter


def test_local_queue_contract_publish_consume():
    queue = LocalQueueAdapter()
    received = []

    async def run():
        await queue.publish("test-queue", {"id": "msg-1"})

        async def handler(message):
            received.append(message.body)

        await queue.consume("test-queue", handler, max_messages=1, wait_time_seconds=1)

    asyncio.run(run())
    assert received == [{"id": "msg-1"}]
