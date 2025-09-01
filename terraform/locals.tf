
locals {
  # From cognito.tf
  cognito_user_pool_id  = aws_cognito_user_pool.amaris_user_pool.id
  cognito_client_id     = aws_cognito_user_pool_client.amaris_user_pool_client.id
  cognito_client_secret = aws_cognito_user_pool_client.amaris_user_pool_client.client_secret

  # From mongo.tf
  mongo_uri = "mongodb://${aws_docdb_cluster.amaris_docdb.master_username}:${random_password.mongo_password.result}@${aws_docdb_cluster.amaris_docdb.endpoint}:27017"
  mongo_db  = "amaris"

  # From ses.tf
  ses_email = aws_ses_email_identity.amaris_email.email
}
