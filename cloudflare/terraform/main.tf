locals {
  worker_bundle = "${path.module}/../worker/dist/index.mjs"
  bundle_sha    = filesha256(local.worker_bundle)
}

resource "cloudflare_worker" "badge" {
  account_id = var.account_id
  name       = var.worker_name

  observability = {
    enabled            = true
    head_sampling_rate = 1
  }

  subdomain = {
    enabled          = var.enable_workers_dev
    previews_enabled = false
  }
}

resource "terraform_data" "worker_bootstrap" {
  triggers_replace = {
    worker_id  = cloudflare_worker.badge.id
    class_name = var.container_class_name
  }

  provisioner "local-exec" {
    command     = "${path.module}/scripts/worker-bootstrap.sh"
    interpreter = ["/usr/bin/env", "bash", "-c"]
    environment = {
      CF_ACCOUNT_ID         = var.account_id
      CF_WORKER_NAME        = cloudflare_worker.badge.name
      CF_CLASS_NAME         = var.container_class_name
      CF_BUNDLE             = local.worker_bundle
      CF_COMPATIBILITY_DATE = var.compatibility_date
    }
  }
}

resource "cloudflare_worker_version" "badge" {
  account_id = var.account_id
  worker_id  = cloudflare_worker.badge.id

  main_module         = "index.mjs"
  compatibility_date  = var.compatibility_date
  compatibility_flags = ["nodejs_compat"]

  modules = [{
    name         = "index.mjs"
    content_type = "application/javascript+module"
    content_file = local.worker_bundle
  }]

  containers = [{
    class_name = var.container_class_name
  }]

  bindings = [
    {
      type       = "durable_object_namespace"
      name       = "GHCR_BADGE"
      class_name = var.container_class_name
    },
    {
      type = "plain_text"
      name = "APP_VERSION"
      text = var.app_version
    },
    {
      type = "plain_text"
      name = "CACHE_TTL"
      text = tostring(var.cache_ttl_seconds)
    },
    {
      type = "plain_text"
      name = "BROWSER_TTL"
      text = tostring(var.browser_ttl_seconds)
    },
    {
      type = "plain_text"
      name = "CONTAINER_SLEEP_AFTER"
      text = var.container_sleep_after
    },
    {
      type         = "ratelimit"
      name         = "RL_MISS"
      namespace_id = "1001"
      simple = {
        limit  = var.rate_limit_miss
        period = 60
      }
    },
  ]

  limits = {
    cpu_ms = 30000
  }

  annotations = {
    workers_message = "ghcr-badge ${var.app_version}, image ${var.container_image}"
    workers_tag     = substr(local.bundle_sha, 0, 16)
  }

  depends_on = [terraform_data.worker_bootstrap]

  lifecycle {
    ignore_changes = [bindings]
  }
}

resource "cloudflare_workers_deployment" "badge" {
  account_id  = var.account_id
  script_name = cloudflare_worker.badge.name
  strategy    = "percentage"

  versions = [{
    version_id = cloudflare_worker_version.badge.id
    percentage = 100
  }]

  annotations = {
    workers_message = "ghcr-badge ${var.app_version}"
  }
}

resource "cloudflare_workers_custom_domain" "badge" {
  count = var.enable_custom_domain ? 1 : 0

  account_id = var.account_id
  zone_id    = local.zone_id
  zone_name  = var.zone_name
  hostname   = var.hostname
  service    = cloudflare_worker.badge.name

  depends_on = [cloudflare_workers_deployment.badge]
}
