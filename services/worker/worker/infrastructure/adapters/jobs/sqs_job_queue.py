"""SQS adapter for worker job queueing."""
from __future__ import annotations

from worker.domain.ports.job_repository import JobQueue
from worker.shared.aws_clients import SQSClient


class SqsJobQueue(JobQueue):
    def __init__(self, client: SQSClient | None = None) -> None:
        self._client = client or SQSClient()

    def enqueue(self, *, job_id: str, job_type: str, payload: dict) -> None:
        self._client.send_message({
            "job_id": str(job_id),
            "job_type": job_type,
            "payload": payload,
        })
