# The Worker existed before the state moved to R2, so the first apply adopts
# it instead of failing on its name. Terraform ignores an import block whose
# target is already in state, so this stays here on purpose: if the state is
# ever lost, `terraform apply` adopts the Worker again.
#
# Nothing else needs adopting. The version and the deployment are created
# anew, which deploys the bundle once more. terraform_data.worker_bootstrap
# finds the Durable Object namespace and does nothing, and
# terraform_data.container_app updates the application it finds by name and
# rolls it out. The hostname is the egpl.dev repository's.
import {
  to = cloudflare_worker.badge
  id = "${var.account_id}/${var.worker_name}"
}
