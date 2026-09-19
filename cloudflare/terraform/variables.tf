variable "account_id" {
  type        = string
  description = "Cloudflare account ID that owns the Worker and the container."
}

variable "zone_id" {
  type        = string
  default     = ""
  description = "Pin the zone by ID instead of looking it up by name. Rarely needed."
}

variable "zone_name" {
  type        = string
  default     = "egpl.dev"
  description = "Zone apex. The zone and its DNS records are managed in the iac repository; this only looks the zone up."
}

variable "hostname" {
  type        = string
  description = <<-EOT
    Hostname the badges are served on, e.g. ghcr-badge.egpl.dev. Must be inside
    zone_name, and must have no DNS record of its own in the iac repository: the
    Workers custom domain creates and owns that record (see enable_custom_domain).
  EOT
}

variable "enable_custom_domain" {
  type        = bool
  default     = true
  description = <<-EOT
    Attach the Worker to hostname as a Workers custom domain. That creates the
    DNS record and refuses to while another record (the CNAME to Render) still
    holds the name. Set false, with enable_workers_dev = true, to deploy the
    Worker and the container first and try them on *.workers.dev while DNS
    still points at the old deployment.
  EOT
}

variable "enable_workers_dev" {
  type        = bool
  default     = false
  description = <<-EOT
    Also serve the Worker on its *.workers.dev hostname.

    Useful before the zone's nameservers have moved. Understand what it costs:
    workers.dev is not a zone you own, so the rate limiting rule in security.tf
    does not apply to it. The Worker's own per-IP limit is all that is left, and
    the hostname is a second door to the same container. Leave it off in
    production.
  EOT
}

variable "worker_name" {
  type        = string
  default     = "ghcr-badge"
  description = "Name of the Worker script."
}

variable "compatibility_date" {
  type        = string
  default     = "2026-09-01"
  description = "Workers compatibility date of the gateway."
}

variable "app_version" {
  type        = string
  description = "The ghcr-badge release being served, e.g. 2.0.0. Shown by /health; passed in by mise from the latest tag."
}

variable "container_image" {
  type        = string
  description = <<-EOT
    Image reference for the badge server, e.g. ghcr-badge:2.0.0. A bare name:tag
    is resolved against the Cloudflare managed registry
    (registry.cloudflare.com/<account_id>/...). Push it first with `mise run push`.
  EOT
}

variable "container_app_name" {
  type        = string
  default     = "ghcr-badge"
  description = "Name of the container application."
}

variable "container_class_name" {
  type        = string
  default     = "GhcrBadgeContainer"
  description = "Durable Object class the container is attached to. Must match the class exported by the Worker."
}

variable "container_instance_type" {
  type        = string
  default     = "lite"
  description = <<-EOT
    Predefined instance type: lite (1/16 vCPU, 256 MiB, 2 GB), basic (1/4 vCPU,
    1 GiB, 4 GB), standard-1 … standard-4. The badge server is FastAPI + uvicorn
    at a few tens of MB of RSS, and its image unpacks to well under 2 GB, so
    lite is enough. Memory and disk are billed for as long as an instance runs.
  EOT

  validation {
    condition     = contains(["lite", "basic", "standard-1", "standard-2", "standard-3", "standard-4"], var.container_instance_type)
    error_message = "container_instance_type must be one of lite, basic, standard-1, standard-2, standard-3, standard-4."
  }
}

variable "container_max_instances" {
  type        = number
  default     = 1
  description = "Upper bound on simultaneously running instances. The Worker always addresses one."
}

variable "container_sleep_after" {
  type        = string
  default     = "10m"
  description = <<-EOT
    Idle time before the instance is stopped. The image is small, so a cold
    start costs a second or two; shorter cuts the bill when the edge cache is
    absorbing the traffic, longer keeps the server warm for a burst of misses.
  EOT
}

variable "cache_ttl_seconds" {
  type        = number
  default     = 600
  description = <<-EOT
    How long a badge is kept in the edge cache. A badge changes only when a new
    image is pushed to ghcr.io, so this is how stale a tag list or a size may be.
  EOT
}

variable "browser_ttl_seconds" {
  type        = number
  default     = 300
  description = "max-age sent to clients. GitHub's Camo keeps a badge for about this long before asking again."
}

variable "rate_limit_miss" {
  type        = number
  default     = 60
  description = "Cache misses per 60 s per IP, per colo. Hits are never counted."
}

variable "zone_rate_limit_requests" {
  type        = number
  default     = 100
  description = "Zone-level rate limiting rule: requests per 10 s per IP, per colo, before the rule blocks. Camo fetches every badge of a README at once, so leave room for a page of them."
}

variable "zone_rate_limit_mitigation_timeout" {
  type        = number
  default     = 10
  description = <<-EOT
    How long the block lasts once the zone rate limit trips, in seconds. The
    Free plan only allows 10; Pro allows up to an hour, Business up to a day.
  EOT
}

variable "enable_zone_rules" {
  type        = bool
  default     = false
  description = <<-EOT
    Manage the zone-level rate limiting ruleset. A zone holds one ruleset per
    phase, so this can only be true when nothing else owns http_ratelimit on
    the zone (on egpl.dev, dbpedia-japanese-mirror's Terraform does — add a
    rule for this hostname there instead). Off, the Worker's own per-IP limit
    on cache misses is the only rate limit, which is enough for a badge server.
  EOT
}
