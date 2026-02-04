import boto3
from botocore.exceptions import ClientError
from worker.config import settings
import structlog

logger = structlog.get_logger()


class SQSClient:
    def __init__(self):
        self.client = boto3.client(
            "sqs",
            region_name=settings.aws_region,
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.queue_url = self._resolve_queue(
            queue_name=settings.sqs_queue_name,
            create_if_missing=True,
        )
        self.queue_high_url = self._resolve_queue(
            queue_name=settings.sqs_queue_high_priority_name,
            create_if_missing=True,
            fallback=self.queue_url,
        )
        logger.info(
            "sqs_client_initialized",
            queue=self.queue_url,
            queue_high=self.queue_high_url,
        )

    def _resolve_queue(self, queue_name: str, create_if_missing: bool, fallback: str | None = None) -> str:
        try:
            response = self.client.get_queue_url(QueueName=queue_name)
            return response["QueueUrl"]
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if create_if_missing and error_code == "AWS.SimpleQueueService.NonExistentQueue":
                response = self.client.create_queue(QueueName=queue_name)
                return response["QueueUrl"]
            if fallback:
                logger.warning("queue_missing_fallback", requested=queue_name, fallback=fallback)
                return fallback
            logger.error("sqs_queue_resolution_failed", queue=queue_name, exc_info=exc)
            raise
    
    def receive_messages(self, queue_url=None, max_messages=1, wait_time=20):
        """
        Receive messages from SQS queue.
        Uses long polling (wait_time=20s) for efficiency.
        """
        target_queue = queue_url if queue_url else self.queue_url
        
        response = self.client.receive_message(
            QueueUrl=target_queue,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time,
            VisibilityTimeout=settings.sqs_visibility_timeout_seconds,
            MessageAttributeNames=['All']
        )
        
        return response.get('Messages', [])
    
    def delete_message(self, receipt_handle, queue_url=None):
        """Delete message from queue after successful processing"""
        target_queue = queue_url if queue_url else self.queue_url
        self.client.delete_message(
            QueueUrl=target_queue,
            ReceiptHandle=receipt_handle
        )
        logger.info("message_deleted", receipt_handle=receipt_handle[:20])
    
    def change_message_visibility(self, receipt_handle, visibility_timeout, queue_url=None):
        """Change message visibility timeout (for extending processing time)"""
        target_queue = queue_url if queue_url else self.queue_url
        self.client.change_message_visibility(
            QueueUrl=target_queue,
            ReceiptHandle=receipt_handle,
            VisibilityTimeout=visibility_timeout
        )

    def send_message(self, message_body, queue_url=None):
        """Send message to queue"""
        import json
        if isinstance(message_body, dict):
            message_body = json.dumps(message_body)
            
        target_queue = queue_url if queue_url else self.queue_url
        self.client.send_message(
            QueueUrl=target_queue,
            MessageBody=message_body
        )


class S3Client:
    def __init__(self):
        self.client = boto3.client(
            's3',
            region_name=settings.aws_region,
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        
        # For LocalStack
        if settings.s3_force_path_style:
            self.client = boto3.client(
                's3',
                region_name=settings.aws_region,
                endpoint_url=settings.aws_endpoint_url,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                config=boto3.session.Config(s3={'addressing_style': 'path'})
            )
        
        self.bucket = settings.s3_bucket
        logger.info("s3_client_initialized", bucket=self.bucket)
    
    def upload_file(self, file_path, s3_key):
        """Upload file to S3"""
        self.client.upload_file(file_path, self.bucket, s3_key)
        logger.info("file_uploaded", s3_key=s3_key)
        return f"s3://{self.bucket}/{s3_key}"
    
    def generate_presigned_url(self, s3_key, expires_in=900):
        """Generate presigned URL for S3 object"""
        url = self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': s3_key},
            ExpiresIn=expires_in
        )
        return url

    def upload_json(self, s3_key: str, data: dict):
        """Upload JSON data to S3"""
        import json
        body = json.dumps(data, default=str)
        self.client.put_object(
            Bucket=self.bucket,
            Key=s3_key,
            Body=body,
            ContentType='application/json'
        )
        logger.info("json_uploaded", s3_key=s3_key)
        return f"s3://{self.bucket}/{s3_key}"

    def object_exists(self, s3_key: str) -> bool:
        """Check if object exists in S3"""
        try:
            self.client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    def get_json(self, s3_key: str) -> dict | None:
        """Get JSON data from S3"""
        import json
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=s3_key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise
