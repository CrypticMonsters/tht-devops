locals {
  order_api_tag = try(data.aws_ecr_image.order_api.image_tags[0], "latest")
  processor_tag = try(data.aws_ecr_image.processor.image_tags[0], "latest")
}

resource "aws_ecs_cluster" "main" {
  name = "${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
###################### ECS SERVICES AND TASK DEFINITIONS HERE

# Order Processor API
#####################
resource "aws_ecs_task_definition" "processor" {
  family                   = "${var.environment}-processor"
  requires_compatibilities = ["EC2"]
  network_mode             = "bridge"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "processor"
      image     = "${data.aws_ecr_repository.processor.repository_url}:${local.processor_tag}"
      essential = true

      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "AWS_DEFAULT_REGION"
          value = var.aws_region
        },
        {
          name  = "DYNAMODB_ENDPOINT"
          value = "https://dynamodb.${var.aws_region}.amazonaws.com"
        },
        {
          name  = "DYNAMODB_TABLE"
          value = var.inventory_table_name
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.data_processor_api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "processor"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "processor" {
  name            = "${var.environment}-processor"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.processor.arn
  desired_count   = 1

  capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.main.name
    weight            = 100
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  service_registries {
    registry_arn   = aws_service_discovery_service.processor.arn
    container_name = "processor"
    container_port = 8000
  }
}

# Order API
###########
resource "aws_ecs_task_definition" "order_api" {
  family                   = "${var.environment}-order-api"
  requires_compatibilities = ["EC2"]
  network_mode             = "bridge"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "order-api"
      image     = "${data.aws_ecr_repository.order_api.repository_url}:${local.order_api_tag}"
      essential = true

      portMappings = [
        {
          containerPort = 8000
          hostPort      = 0 # Dynamic port mapping
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "AWS_DEFAULT_REGION"
          value = var.aws_region
        },
        {
          name  = "DYNAMODB_ENDPOINT"
          value = "https://dynamodb.${var.aws_region}.amazonaws.com"
        },
        {
          name  = "DYNAMODB_TABLE"
          value = var.orders_table_name
        },
        {
          name  = "SRV_ENDPOINT"
          value = "${aws_service_discovery_service.processor.name}.${aws_service_discovery_private_dns_namespace.main.name}"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.order_api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "order-api"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "order_api" {
  name            = "${var.environment}-order-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.order_api.arn
  desired_count   = 1

  capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.main.name
    weight            = 100
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.order_api.arn
    container_name   = "order-api"
    container_port   = 8000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
}
