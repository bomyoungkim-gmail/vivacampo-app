#!/bin/bash
set -euo pipefail

awslocal s3 mb s3://vivacampo-derived-local || true

awslocal sqs create-queue --queue-name vivacampo-jobs-dlq >/dev/null || true
DLQ_URL=$(awslocal sqs get-queue-url --queue-name vivacampo-jobs-dlq --query 'QueueUrl' --output text)
DLQ_ARN=$(awslocal sqs get-queue-attributes --queue-url "$DLQ_URL" --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

awslocal sqs create-queue --queue-name vivacampo-jobs >/dev/null || true
Q_URL=$(awslocal sqs get-queue-url --queue-name vivacampo-jobs --query 'QueueUrl' --output text)

awslocal sqs set-queue-attributes \
  --queue-url "$Q_URL" \
  --attributes '{"RedrivePolicy":"{\"deadLetterTargetArn\":\"'"$DLQ_ARN"'\",\"maxReceiveCount\":\"3\"}"}'

awslocal sqs set-queue-attributes \
  --queue-url "$Q_URL" \
  --attributes '{"VisibilityTimeout":"900"}'

echo "[localstack-init] S3+SQS ready"
