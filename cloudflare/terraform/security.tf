locals {
  on_endpoint = "http.host eq \"${var.hostname}\""
}

resource "cloudflare_ruleset" "ratelimit" {
  count = var.enable_zone_rules ? 1 : 0

  zone_id     = local.zone_id
  name        = "${var.worker_name} rate limit"
  description = "Blunt per-IP ceiling in front of the Worker"
  kind        = "zone"
  phase       = "http_ratelimit"

  rules = [
    {
      ref         = "badge_per_ip"
      description = "Per-IP request ceiling on the whole hostname"
      expression  = local.on_endpoint
      action      = "block"

      ratelimit = {
        characteristics     = ["ip.src", "cf.colo.id"]
        period              = 10
        requests_per_period = var.zone_rate_limit_requests
        mitigation_timeout  = var.zone_rate_limit_mitigation_timeout
      }
    },
  ]
}
