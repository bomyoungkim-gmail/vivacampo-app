import boto3
from botocore.config import Config
from app.config import settings
from app.infrastructure.resilience import retry_with_backoff_sync, circuit_sync

class SQSClientWrapper:
    def __init__(self):
        config = Config(
            connect_timeout=settings.aws_connect_timeout_seconds,
            read_timeout=settings.aws_read_timeout_seconds,
        )
        self.client = boto3.client(
            "sqs",
            region_name=settings.aws_region,
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=config,
        )

    @retry_with_backoff_sync(max_attempts=3, initial_delay=1.0, max_delay=8.0)
    @circuit_sync(failure_threshold=3, recovery_timeout=120)
    def send_message(self, queue_name_or_url: str, body: str):
        # If queue_name_or_url is a name, we might need to get the URL first.
        # But commonly localstack/aws can take URL. 
        # If it's just a name, we should resolve it. 
        # For simplicity, assuming the config provides a URL or we resolve it.
        # However, typically 'get_queue_url' is needed if we only have name.
        
        # Let's assume queue_url is passed or we resolve it blindly.
        # Actually LocalStack usually works with QueueUrl which matches endpoint + name.
        
        if not queue_name_or_url.startswith("http"):
            try:
                response = self.client.get_queue_url(QueueName=queue_name_or_url)
                queue_url = response["QueueUrl"]
            except Exception:
                # Fallback or error
                queue_url = f"{settings.aws_endpoint_url}/queue/{queue_name_or_url}" if settings.aws_endpoint_url else queue_name_or_url
        else:
            queue_url = queue_name_or_url

        return self.client.send_message(
            QueueUrl=queue_url,
            MessageBody=body
        )

def get_sqs_client():
    return SQSClientWrapper()
