# Get ECR repository information
data "aws_ecr_repository" "order_api" {
  name = var.order_api_repository_name
}

data "aws_ecr_repository" "processor" {
  name = var.processor_repository_name
}

resource "aws_iam_role_policy" "ecr_pull_policy" {
  name = "${var.environment}-ecr-pull-policy"
  role = aws_iam_role.ecs_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchCheckLayerAvailability"
        ]
        Resource = [
          data.aws_ecr_repository.order_api.arn,
          data.aws_ecr_repository.processor.arn
        ]
      }
    ]
  })
}
