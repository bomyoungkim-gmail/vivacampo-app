import boto3
from worker.config import settings
import structlog

logger = structlog.get_logger()


class SQSClient:
    def __init__(self):
        self.client = boto3.client(
            'sqs',
            region_name=settings.aws_region,
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        
        # Get queue URL
        try:
             response = self.client.get_queue_url(QueueName=settings.sqs_queue_name)
             self.queue_url = response['QueueUrl']
             
             # Try getting High Priority Queue (might not exist in localstack yet, but we handle it)
             try:
                 resp_high = self.client.get_queue_url(QueueName=settings.sqs_queue_high_priority_name)
                 self.queue_high_url = resp_high['QueueUrl']
             except:
                 # Auto-create if missing (dev convenience)
                 resp_high = self.client.create_queue(QueueName=settings.sqs_queue_high_priority_name)
                 self.queue_high_url = resp_high['QueueUrl']

             logger.info("sqs_client_initialized", queue=self.queue_url, queue_high=self.queue_high_url)
        except Exception as e:
             logger.error("sqs_init_error", exc_info=e)
             raise e
    
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
