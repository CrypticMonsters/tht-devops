resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "${var.environment}.internal"
  vpc         = var.vpc_id
  description = "Private DNS namespace for service discovery"
}

resource "aws_service_discovery_service" "processor" {
  name = "processor"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "SRV"
    }
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}
