output "queue_urls" {
  value = [for q in aws_sqs_queue.this : q.id]
}
