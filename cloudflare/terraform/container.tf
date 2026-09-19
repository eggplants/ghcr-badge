resource "terraform_data" "container_app" {
  triggers_replace = {
    account_id     = var.account_id
    app_name       = var.container_app_name
    worker_name    = cloudflare_worker.badge.name
    class_name     = var.container_class_name
    image          = var.container_image
    instance_type  = var.container_instance_type
    max_instances  = var.container_max_instances
    worker_version = cloudflare_worker_version.badge.id
    script         = filesha256("${path.module}/scripts/container-app.sh")
  }

  provisioner "local-exec" {
    command     = "${path.module}/scripts/container-app.sh apply"
    interpreter = ["/usr/bin/env", "bash", "-c"]
    environment = {
      CF_ACCOUNT_ID    = self.triggers_replace.account_id
      CF_APP_NAME      = self.triggers_replace.app_name
      CF_WORKER_NAME   = self.triggers_replace.worker_name
      CF_CLASS_NAME    = self.triggers_replace.class_name
      CF_IMAGE         = self.triggers_replace.image
      CF_INSTANCE_TYPE = self.triggers_replace.instance_type
      CF_MAX_INSTANCES = self.triggers_replace.max_instances
    }
  }

  provisioner "local-exec" {
    when        = destroy
    command     = "${path.module}/scripts/container-app.sh destroy"
    interpreter = ["/usr/bin/env", "bash", "-c"]
    on_failure  = continue
    environment = {
      CF_ACCOUNT_ID = self.triggers_replace.account_id
      CF_APP_NAME   = self.triggers_replace.app_name
    }
  }

  depends_on = [cloudflare_workers_deployment.badge]
}
