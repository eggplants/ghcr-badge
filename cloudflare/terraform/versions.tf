terraform {
  # The S3 backend's use_lockfile is generally available from 1.11.
  required_version = ">= 1.11.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.25"
    }
  }

  # State lives in R2, in the bucket the egpl.dev repository keeps its own
  # state in (scripts/create-state-bucket.sh there), under this repository's
  # name. R2 is not S3: it has no regions, STS, metadata service or account
  # IDs, hence the skip_* flags, and it wants path-style addressing. Locking
  # uses the S3 backend's lock file (conditional PutObject), which R2 supports.
  # Credentials arrive as AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY from
  # ../.env — see ../scripts/create-api-token.sh. The endpoint names the
  # account and cannot be a variable here; it is not secret. A fork points it
  # at its own account and bucket.
  backend "s3" {
    bucket = "terraform-state"
    key    = "ghcr-badge/terraform.tfstate"
    region = "auto"
    endpoints = {
      s3 = "https://c366607138eaf26251e3ffe59a059dec.r2.cloudflarestorage.com"
    }
    use_path_style              = true
    use_lockfile                = true
    skip_credentials_validation = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
    skip_s3_checksum            = true
  }
}

# CLOUDFLARE_API_TOKEN is read from the environment: mise.toml sets it from
# ../.env through ../scripts/cf-token.sh. ../scripts/create-api-token.sh
# creates that token with the permission groups this configuration needs, and
# derives the R2 credentials for the backend from it.
provider "cloudflare" {}
