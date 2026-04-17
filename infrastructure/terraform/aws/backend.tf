# Backend Infrastructure
# API Gateway + DynamoDB + Lambda Functions

# ============================================================
# DynamoDB Tables (16 total)
# ============================================================

# --- KEPT Tables (7) ---
# config, audit_log, users, organizations, org_invitations,
# notifications, subscription_plans

resource "aws_dynamodb_table" "config" {
  name         = "${local.resource_prefix}-config"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }
  attribute {
    name = "sk"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = { Name = "${local.resource_prefix}-config" }
}

resource "aws_dynamodb_table" "audit_log" {
  name         = "${local.resource_prefix}-audit-log"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  range_key    = "timestamp"

  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "S"
  }
  attribute {
    name = "userId"
    type = "S"
  }
  attribute {
    name = "org_id"
    type = "S"
  }

  global_secondary_index {
    name            = "UserIdIndex"
    hash_key        = "userId"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "OrgIdIndex"
    hash_key        = "org_id"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expiresAt"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  tags = { Name = "${local.resource_prefix}-audit-log" }
}

resource "aws_dynamodb_table" "users" {
  name         = "${local.resource_prefix}-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "email"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }
  attribute {
    name = "org_id"
    type = "S"
  }
  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "EmailIndex"
    hash_key        = "email"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "status"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "OrgIdIndex"
    hash_key        = "org_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-users" })
}

resource "aws_dynamodb_table" "organizations" {
  name         = "${local.resource_prefix}-organizations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "slug"
    type = "S"
  }
  attribute {
    name = "owner_id"
    type = "S"
  }
  attribute {
    name = "stripe_customer_id"
    type = "S"
  }

  global_secondary_index {
    name            = "SlugIndex"
    hash_key        = "slug"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "OwnerIdIndex"
    hash_key        = "owner_id"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "StripeCustomerIndex"
    hash_key        = "stripe_customer_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-organizations" })
}

resource "aws_dynamodb_table" "org_invitations" {
  name         = "${local.resource_prefix}-org-invitations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "org_id"
    type = "S"
  }
  attribute {
    name = "email"
    type = "S"
  }
  attribute {
    name = "token"
    type = "S"
  }
  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "OrgIdIndex"
    hash_key        = "org_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "EmailIndex"
    hash_key        = "email"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "TokenIndex"
    hash_key        = "token"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expires_at_ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-org-invitations" })
}

resource "aws_dynamodb_table" "notifications" {
  name         = "${local.resource_prefix}-notifications"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "timestamp_id"

  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "timestamp_id"
    type = "S"
  }
  attribute {
    name = "org_id"
    type = "S"
  }

  global_secondary_index {
    name            = "OrgIdIndex"
    hash_key        = "org_id"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expires_at_ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-notifications" })
}

resource "aws_dynamodb_table" "subscription_plans" {
  name         = "${local.resource_prefix}-subscription-plans"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-subscription-plans" })
}

# --- NEW Document Processing Tables (9) ---

# Documents: stores uploaded documents per user
resource "aws_dynamodb_table" "documents" {
  name         = "${local.resource_prefix}-documents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "id"

  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }
  attribute {
    name = "embedding_model_id"
    type = "S"
  }

  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "user_id"
    range_key       = "status"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "EmbeddingModelIndex"
    hash_key        = "embedding_model_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-documents" })
}

# Document chunks: chunked text from parsed documents for embedding
resource "aws_dynamodb_table" "document_chunks" {
  name         = "${local.resource_prefix}-document-chunks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "document_id"
  range_key    = "chunk_id"

  attribute {
    name = "document_id"
    type = "S"
  }
  attribute {
    name = "chunk_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-document-chunks" })
}

# Models: AI model configurations per user (LLM, embedding, etc.)
resource "aws_dynamodb_table" "models" {
  name         = "${local.resource_prefix}-models"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "id"

  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "model_type"
    type = "S"
  }

  global_secondary_index {
    name            = "TypeIndex"
    hash_key        = "user_id"
    range_key       = "model_type"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-models" })
}

# Pipelines: document processing pipeline definitions per user
resource "aws_dynamodb_table" "pipelines" {
  name         = "${local.resource_prefix}-pipelines"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "id"

  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "user_id"
    range_key       = "status"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-pipelines" })
}

# Pipeline documents: many-to-many link between pipelines and documents
resource "aws_dynamodb_table" "pipeline_documents" {
  name         = "${local.resource_prefix}-pipeline-documents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pipeline_id"
  range_key    = "document_id"

  attribute {
    name = "pipeline_id"
    type = "S"
  }
  attribute {
    name = "document_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-pipeline-documents" })
}

# Outputs: structured extraction results from pipeline runs
resource "aws_dynamodb_table" "outputs" {
  name         = "${local.resource_prefix}-outputs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pipeline_id"
  range_key    = "id"

  attribute {
    name = "pipeline_id"
    type = "S"
  }
  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-outputs" })
}

# Queries: user queries against pipelines/documents
resource "aws_dynamodb_table" "queries" {
  name         = "${local.resource_prefix}-queries"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "id"

  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "pipeline_id"
    type = "S"
  }

  global_secondary_index {
    name            = "PipelineIndex"
    hash_key        = "pipeline_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-queries" })
}

# Usage tracking: tracks API/model usage per user per billing period
resource "aws_dynamodb_table" "usage_tracking" {
  name         = "${local.resource_prefix}-usage-tracking"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "period"

  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "period"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-usage-tracking" })
}

# Plan models: maps subscription plans to available AI models
resource "aws_dynamodb_table" "plan_models" {
  name         = "${local.resource_prefix}-plan-models"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "plan_id"
  range_key    = "model_id"

  attribute {
    name = "plan_id"
    type = "S"
  }
  attribute {
    name = "model_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-plan-models" })
}

# ============================================================
# S3 Bucket for uploads
# ============================================================

resource "aws_s3_bucket" "uploads" {
  bucket = "${local.resource_prefix}-uploads-${data.aws_caller_identity.current.account_id}"
  tags   = { Name = "${local.resource_prefix}-uploads" }
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket                  = aws_s3_bucket.uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================
# IAM Role for Lambda
# ============================================================

resource "aws_iam_role" "lambda_execution" {
  name = "${local.resource_prefix}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = { Name = "${local.resource_prefix}-lambda-execution-role" }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_custom" {
  name = "${local.resource_prefix}-lambda-custom-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBAccess"
        Effect = "Allow"
        Action = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:DeleteItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:BatchGetItem", "dynamodb:BatchWriteItem", "dynamodb:DescribeTable"]
        Resource = [
          # Kept tables
          aws_dynamodb_table.config.arn, "${aws_dynamodb_table.config.arn}/index/*",
          aws_dynamodb_table.audit_log.arn, "${aws_dynamodb_table.audit_log.arn}/index/*",
          aws_dynamodb_table.users.arn, "${aws_dynamodb_table.users.arn}/index/*",
          aws_dynamodb_table.organizations.arn, "${aws_dynamodb_table.organizations.arn}/index/*",
          aws_dynamodb_table.org_invitations.arn, "${aws_dynamodb_table.org_invitations.arn}/index/*",
          aws_dynamodb_table.notifications.arn, "${aws_dynamodb_table.notifications.arn}/index/*",
          aws_dynamodb_table.subscription_plans.arn, "${aws_dynamodb_table.subscription_plans.arn}/index/*",
          # New document processing tables
          aws_dynamodb_table.documents.arn, "${aws_dynamodb_table.documents.arn}/index/*",
          aws_dynamodb_table.document_chunks.arn, "${aws_dynamodb_table.document_chunks.arn}/index/*",
          aws_dynamodb_table.models.arn, "${aws_dynamodb_table.models.arn}/index/*",
          aws_dynamodb_table.pipelines.arn, "${aws_dynamodb_table.pipelines.arn}/index/*",
          aws_dynamodb_table.pipeline_documents.arn, "${aws_dynamodb_table.pipeline_documents.arn}/index/*",
          aws_dynamodb_table.outputs.arn, "${aws_dynamodb_table.outputs.arn}/index/*",
          aws_dynamodb_table.queries.arn, "${aws_dynamodb_table.queries.arn}/index/*",
          aws_dynamodb_table.usage_tracking.arn, "${aws_dynamodb_table.usage_tracking.arn}/index/*",
          aws_dynamodb_table.plan_models.arn, "${aws_dynamodb_table.plan_models.arn}/index/*",
        ]
      },
      {
        Sid      = "S3Access"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = [aws_s3_bucket.uploads.arn, "${aws_s3_bucket.uploads.arn}/*"]
      },
      {
        Sid      = "SecretsManagerAccess"
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = ["arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${local.resource_prefix}*"]
      },
      {
        Sid    = "CognitoAccess"
        Effect = "Allow"
        Action = [
          "cognito-idp:SignUp",
          "cognito-idp:InitiateAuth",
          "cognito-idp:ConfirmSignUp",
          "cognito-idp:AdminConfirmSignUp",
          "cognito-idp:ForgotPassword",
          "cognito-idp:ConfirmForgotPassword",
          "cognito-idp:AdminGetUser",
          "cognito-idp:GlobalSignOut",
          "cognito-idp:AdminCreateUser",
          "cognito-idp:AdminSetUserPassword",
          "cognito-idp:AdminUpdateUserAttributes",
          "cognito-idp:RespondToAuthChallenge"
        ]
        Resource = [aws_cognito_user_pool.main.arn]
      },
      {
        Sid      = "SESAccess"
        Effect   = "Allow"
        Action   = ["ses:SendEmail", "ses:SendRawEmail"]
        Resource = ["*"]
      }
    ]
  })
}

# ============================================================
# Placeholder Lambda Package
# ============================================================

data "archive_file" "lambda_placeholder" {
  type        = "zip"
  output_path = "${path.module}/placeholder.zip"

  source {
    content  = <<-EOF
      def handler(event, context):
          return {"statusCode": 200, "body": "Placeholder - deploy code via CI/CD"}
    EOF
    filename = "placeholder.py"
  }
}

# ============================================================
# API Gateway
# ============================================================

resource "aws_apigatewayv2_api" "main" {
  name          = "${local.resource_prefix}-api"
  protocol_type = "HTTP"
  description   = "API Gateway for ${var.project_name} ${var.environment}"

  cors_configuration {
    allow_origins     = ["*"]
    allow_methods     = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers     = ["Content-Type", "Authorization", "X-Amz-Date", "X-Api-Key", "X-Org-Id"]
    expose_headers    = ["*"]
    max_age           = 300
    allow_credentials = false
  }

  tags = { Name = "${local.resource_prefix}-api" }
}

resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.environment
  auto_deploy = true

  default_route_settings {
    throttling_rate_limit  = var.api_throttling_rate_limit
    throttling_burst_limit = var.api_throttling_burst_limit
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
    })
  }

  tags = { Name = "${local.resource_prefix}-api-stage" }
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${local.resource_prefix}-api"
  retention_in_days = 30
  tags              = { Name = "${local.resource_prefix}-api-logs" }
}

# ============================================================
# Lambda Function
# ============================================================

resource "aws_lambda_function" "api" {
  function_name    = "${local.resource_prefix}-api"
  role             = aws_iam_role.lambda_execution.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_placeholder.output_path
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout

  environment {
    variables = {
      ENVIRONMENT           = var.environment
      AWS_REGION_NAME       = var.aws_region
      COGNITO_USER_POOL_ID  = aws_cognito_user_pool.main.id
      COGNITO_CLIENT_ID     = aws_cognito_user_pool_client.main.id
      UPLOADS_BUCKET        = aws_s3_bucket.uploads.id
      DYNAMODB_TABLE_PREFIX = local.resource_prefix
      CORS_ORIGINS          = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_cloudfront_distribution.frontend.domain_name}"
      API_STAGE             = var.environment
      # Billing
      STRIPE_SECRET_KEY          = var.stripe_secret_key
      STRIPE_WEBHOOK_SECRET      = var.stripe_webhook_secret
      # OAuth
      GOOGLE_OAUTH_CLIENT_ID     = var.google_oauth_client_id
      GOOGLE_OAUTH_CLIENT_SECRET = var.google_oauth_client_secret
      GOOGLE_OAUTH_ENABLED       = var.google_oauth_client_id != "" ? "true" : "false"
      OAUTH_INTERNAL_SECRET      = var.oauth_internal_secret
      # Email
      SES_FROM_EMAIL             = var.ses_from_email
      # AI / Document Processing
      OPENAI_API_KEY             = var.openai_api_key
      PINECONE_API_KEY           = var.pinecone_api_key
      PINECONE_ENVIRONMENT       = var.pinecone_environment
      PINECONE_INDEX_NAME        = var.pinecone_index_name
      ANTHROPIC_API_KEY          = var.anthropic_api_key
    }
  }

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  tags = { Name = "${local.resource_prefix}-api" }
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = 14
  tags              = { Name = "${local.resource_prefix}-lambda-logs" }
}

# ============================================================
# API Gateway Lambda Integration
# ============================================================

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
