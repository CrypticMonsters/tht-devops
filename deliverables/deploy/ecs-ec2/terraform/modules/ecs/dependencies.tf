data "aws_availability_zones" "available" {
  state = "available"
}
data "aws_region" "current" {}

data "aws_ecr_repository" "order_api" {
  name = var.order_api_repository_name
}

data "aws_ecr_repository" "processor" {
  name = var.processor_repository_name
}

data "aws_ecr_image" "order_api" {
  repository_name = data.aws_ecr_repository.order_api.name
  most_recent     = true
}

data "aws_ecr_image" "processor" {
  repository_name = data.aws_ecr_repository.processor.name
  most_recent     = true
}
