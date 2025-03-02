resource "aws_cloudwatch_log_group" "order_api" {
  name = "/ecs/order-api"
  retention_in_days = 7 # Keep logs for 7 days (adjust as needed)
}

resource "aws_cloudwatch_log_group" "data_processor_api" {
  name = "/ecs/data-processor-api"
  retention_in_days = 7 # Keep logs for 7 days (adjust as needed)
}
