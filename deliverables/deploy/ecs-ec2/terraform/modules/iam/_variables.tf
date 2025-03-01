variable "environment" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
}

variable "orders_table_arn" {
  description = "ARN of the Orders DynamoDB table"
  type        = string
}

variable "inventory_table_arn" {
  description = "ARN of the Inventory DynamoDB table"
  type        = string
}

variable "order_api_repository_name" {
  description = "Name of the Order API ECR repository"
  type        = string
}

variable "processor_repository_name" {
  description = "Name of the Order Processor ECR repository"
  type        = string
}

variable "tags" {
  description = "A map of tags to add to all resources."
  type        = map(string)
  default     = {}
}
