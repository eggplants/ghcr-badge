data "cloudflare_zone" "this" {
  count = var.zone_id == "" ? 1 : 0

  filter = {
    account = {
      id = var.account_id
    }
    name = var.zone_name
  }
}

locals {
  zone_id = var.zone_id != "" ? var.zone_id : one(data.cloudflare_zone.this[*].id)
}
