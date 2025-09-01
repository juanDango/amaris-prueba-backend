
variable "ENV" {
  description = "Environment name"
  default     = "prod"
}

variable "region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "ALLOWED_ORIGINS" {
  description = "Allowed origins for CORS"
  default     = "*"
}
