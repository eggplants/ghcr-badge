output "badge_url" {
  value       = "https://${var.hostname}/"
  description = "Where the badges (and the landing page) are served, once the egpl.dev repository has attached the hostname."
}

output "workers_dev_url" {
  value       = var.enable_workers_dev ? cloudflare_worker.badge.subdomain.url : null
  description = "The *.workers.dev address, when enable_workers_dev is true. None of the zone's rules apply to it."
}

output "worker_name" {
  value       = cloudflare_worker.badge.name
  description = "Name of the deployed Worker."
}

output "worker_version_id" {
  value       = cloudflare_worker_version.badge.id
  description = "Version currently receiving 100% of traffic."
}

output "container_application" {
  value       = var.container_app_name
  description = "Container application name. Inspect it with `wrangler containers list`."
}

output "example_request" {
  description = "A badge that should come back immediately."
  value       = "curl -sSI https://${var.hostname}/eggplants/ghcr-badge/tags?trim=major"
}
