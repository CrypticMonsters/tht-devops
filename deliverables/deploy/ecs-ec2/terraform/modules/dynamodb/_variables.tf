variable "environment" {
  description = "Environment name"
  type        = string
}

variable "billing_mode" {
  description = "Billing mode for DynamoDB table"
  type        = string
  default     = "PROVISIONED"
}

variable "read_capacity" {
  description = "Read capacity for DynamoDB table"
  type        = number
  default     = 5
}

variable "write_capacity" {
  description = "Write capacity for DynamoDB table"
  type        = number
  default     = 5
}

variable "tags" {
  description = "A map of tags to add to all resources."
  type        = map(string)
  default     = {}
}
