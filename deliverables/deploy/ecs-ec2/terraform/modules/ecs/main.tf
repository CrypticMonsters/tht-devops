resource "aws_ecs_cluster" "main" {
  name = "${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
###################### ECS SERVICES AND TASK DEFINITIONS HERE
