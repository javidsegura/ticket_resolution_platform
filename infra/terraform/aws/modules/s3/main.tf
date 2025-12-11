resource "aws_s3_bucket" "s3_image_bucket" {
  bucket        = "${var.environment}-${var.project_name}-${random_string.bucket_prefix.result}"
  force_destroy = true

}

resource "random_string" "bucket_prefix" {
  length  = 9
  special = false
  upper   = false

}

resource "aws_s3_bucket_cors_configuration" "configuration_cors" {
  bucket = aws_s3_bucket.s3_image_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "POST", "PUT", "DELETE"]
    allowed_origins = ["*"]
  }
}
