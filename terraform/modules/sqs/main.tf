resource "aws_sqs_queue" "this" {
  for_each = toset(var.queues)
  name     = "vivacampo-${var.environment}-${each.value}"
}
