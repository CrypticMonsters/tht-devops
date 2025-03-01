variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "vpc_id"
  type        = string
}

variable "tags" {
  description = "A map of tags to add to all resources."
  type        = map(string)
  default     = {}
}
