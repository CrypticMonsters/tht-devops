
resource "aws_iam_role_policy" "service_discovery_policy" {
  name = "${var.environment}-service-discovery-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "servicediscovery:RegisterInstance",
          "servicediscovery:DeregisterInstance",
          "servicediscovery:DiscoverInstances",
          "servicediscovery:GetInstancesHealthStatus",
          "route53:GetHealthCheckStatus"
        ]
        Resource = "*"
      }
    ]
  })
}