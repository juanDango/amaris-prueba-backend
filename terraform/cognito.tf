
resource "aws_cognito_user_pool" "amaris_user_pool" {
  name                     = "amaris-user-pool"
  auto_verified_attributes = ["email"]

  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = false
    required            = true
    string_attribute_constraints {
      min_length = 1
      max_length = 2048
    }
  }

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_message        = "Your verification code is {####}."
    email_subject        = "Your verification code"
  }

  tags = {
    Name       = "amaris-user-pool"
    ManagedBy  = local.ManagedBy
    Project    = local.Project
    CostCenter = local.CostCenter
  }
}

resource "aws_cognito_user_pool_client" "amaris_user_pool_client" {
  name                = "amaris-user-pool-client"
  user_pool_id        = aws_cognito_user_pool.amaris_user_pool.id
  generate_secret     = true
  explicit_auth_flows = ["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
}


