resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "${var.environment}.internal"
  vpc         = var.vpc_id
  description = "Private DNS namespace for service discovery"
}

# Use AWS Service Connect to allow ECS tasks to resolve DNS names in the private namespace