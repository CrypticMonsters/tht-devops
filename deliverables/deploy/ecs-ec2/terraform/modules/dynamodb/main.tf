########################################################################################
# Add you Code Here to create a DynamoDB Tables for Orders and Inventory
resource "aws_dynamodb_table" "orders" {
  name = "orders"

  billing_mode   = var.billing_mode
  read_capacity  = var.read_capacity
  write_capacity = var.write_capacity

  hash_key = "order_id"

  attribute {
    name = "order_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "inventory" {
  name = "inventory"

  billing_mode   = var.billing_mode
  read_capacity  = var.read_capacity
  write_capacity = var.write_capacity

  hash_key = "product_id"

  attribute {
    name = "product_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = var.tags
}

# Seed initial inventory data
resource "aws_dynamodb_table_item" "inventory_seed_1" {
  table_name = aws_dynamodb_table.inventory.name
  hash_key   = aws_dynamodb_table.inventory.hash_key

  item = jsonencode({
    "product_id" = { "S" = "PROD001" }
    "name"       = { "S" = "Sample Product 1" }
    "price"      = { "N" = "29" }
    "stock"      = { "N" = "100" }
  })
}

resource "aws_dynamodb_table_item" "inventory_seed_2" {
  table_name = aws_dynamodb_table.inventory.name
  hash_key   = aws_dynamodb_table.inventory.hash_key

  item = jsonencode({
    "product_id" = { "S" = "PROD002" }
    "name"       = { "S" = "Sample Product 2" }
    "price"      = { "N" = "49" }
    "stock"      = { "N" = "50" }
  })
}
