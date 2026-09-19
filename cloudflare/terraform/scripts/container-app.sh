#!/usr/bin/env bash
#
# Creates, updates or deletes the Cloudflare container application that backs
# the ghcr-badge Durable Object. Driven by terraform_data in ../container.tf; see
# the comment there for why this is not a Terraform resource.
#
# Usage: container-app.sh apply | destroy
#
# Environment:
#   CLOUDFLARE_API_TOKEN   token with Workers Scripts:Edit and Containers:Edit
#   CF_ACCOUNT_ID          account that owns the Worker
#   CF_APP_NAME            container application name
#   CF_WORKER_NAME         Worker script the Durable Object lives in   (apply)
#   CF_CLASS_NAME          Durable Object class name                   (apply)
#   CF_IMAGE               image reference, name:tag or a full registry path
#   CF_INSTANCE_TYPE       lite | basic | standard-1..4, default lite  (apply)
#   CF_MAX_INSTANCES                                                  (apply)
set -euo pipefail

API="${CF_API_BASE:-https://api.cloudflare.com/client/v4}"
: "${CLOUDFLARE_API_TOKEN:?CLOUDFLARE_API_TOKEN is not set}"
: "${CF_ACCOUNT_ID:?CF_ACCOUNT_ID is not set}"
: "${CF_APP_NAME:?CF_APP_NAME is not set}"

for cmd in curl jq; do
  command -v "${cmd}" > /dev/null || { echo "[ERROR] ${cmd} is required" >&2; exit 1; }
done

# --- API helper -------------------------------------------------------------
# Prints the `result` of a successful envelope, or the errors and a non-zero
# exit on failure. Cloudflare answers 200 with success=false often enough that
# the HTTP status alone is not a reliable check.
cf_api() {
  local method="$1" path="$2" body="${3:-}"
  local args=(-sS -X "${method}"
    -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}"
    -H "Content-Type: application/json")
  [[ -n "${body}" ]] && args+=(--data "${body}")

  local response
  response="$(curl "${args[@]}" "${API}${path}")"

  if [[ "$(jq -r '.success // false' <<< "${response}")" != "true" ]]; then
    echo "[ERROR] ${method} ${path} failed:" >&2
    jq -r '.errors // .' <<< "${response}" >&2
    return 1
  fi
  jq -c '.result' <<< "${response}"
}

# A bare name:tag means the Cloudflare managed registry, the same de-sugaring
# `wrangler containers push` applies.
resolve_image() {
  local image="$1"
  if [[ "${image}" == *"/"* ]]; then
    printf '%s' "${image}"
  else
    printf 'registry.cloudflare.com/%s/%s' "${CF_ACCOUNT_ID}" "${image}"
  fi
}

find_application_id() {
  cf_api GET "/accounts/${CF_ACCOUNT_ID}/containers/applications" \
    | jq -r --arg name "${CF_APP_NAME}" '[.[] | select(.name == $name)][0].id // empty'
}

# The namespace ID is minted when the Worker version that declares the class is
# deployed, so this has to run after the deployment.
find_namespace_id() {
  cf_api GET "/accounts/${CF_ACCOUNT_ID}/workers/durable_objects/namespaces" \
    | jq -r --arg script "${CF_WORKER_NAME}" --arg class "${CF_CLASS_NAME}" \
        '[.[] | select(.script == $script and .class == $class)][0].id // empty'
}

apply() {
  : "${CF_WORKER_NAME:?CF_WORKER_NAME is not set}"
  : "${CF_CLASS_NAME:?CF_CLASS_NAME is not set}"
  : "${CF_IMAGE:?CF_IMAGE is not set}"

  local image namespace_id configuration
  image="$(resolve_image "${CF_IMAGE}")"

  namespace_id="$(find_namespace_id)"
  if [[ -z "${namespace_id}" ]]; then
    echo "[ERROR] No Durable Object namespace for class '${CF_CLASS_NAME}' in worker '${CF_WORKER_NAME}'." >&2
    echo "        The Worker version has to be deployed before the container application." >&2
    return 1
  fi
  echo "[INFO] Durable Object namespace: ${namespace_id}"
  echo "[INFO] Image: ${image}"

  # A predefined instance type rather than vcpu/memory_mib/disk: custom sizes
  # start at 1 vCPU and 3 GiB, and this server needs a fraction of `lite`.
  configuration="$(jq -n \
    --arg image "${image}" \
    --arg instance_type "${CF_INSTANCE_TYPE:-lite}" \
    '{
      image: $image,
      instance_type: $instance_type,
      observability: { logs: { enabled: true } }
    }')"

  local application_id
  application_id="$(find_application_id)"

  # This is the shape `wrangler deploy` sends for a container attached to a
  # Durable Object class: a scheduler-backed ("default") application that is
  # associated with the namespace through `durable_objects`. The newer
  # `scheduling_policy: "durable_object"` mode takes no configuration at all
  # (images move into the Worker version) and rejects this payload.
  if [[ -z "${application_id}" ]]; then
    echo "[INFO] Creating container application '${CF_APP_NAME}'"
    local payload
    payload="$(jq -n \
      --arg name "${CF_APP_NAME}" \
      --argjson configuration "${configuration}" \
      --argjson max_instances "${CF_MAX_INSTANCES:-1}" \
      --arg namespace_id "${namespace_id}" \
      '{
        name: $name,
        scheduling_policy: "default",
        instances: 0,
        max_instances: $max_instances,
        constraints: { tiers: [1, 2] },
        rollout_active_grace_period: 0,
        configuration: $configuration,
        durable_objects: { namespace_id: $namespace_id }
      }')"
    application_id="$(cf_api POST "/accounts/${CF_ACCOUNT_ID}/containers/applications" "${payload}" | jq -r '.id')"
    echo "[INFO] Created: ${application_id}"
    return 0
  fi

  echo "[INFO] Updating container application '${CF_APP_NAME}' (${application_id})"
  local patch
  patch="$(jq -n \
    --argjson configuration "${configuration}" \
    --argjson max_instances "${CF_MAX_INSTANCES:-1}" \
    '{
      configuration: $configuration,
      max_instances: $max_instances,
      scheduling_policy: "default"
    }')"
  cf_api PATCH "/accounts/${CF_ACCOUNT_ID}/containers/applications/${application_id}" "${patch}" > /dev/null

  # A PATCH records the new configuration; a rollout is what moves the running
  # instances onto it. Without this an image change would only take effect the
  # next time an instance happens to be created.
  echo "[INFO] Rolling out the new configuration"
  local rollout
  rollout="$(jq -n \
    --argjson target "${configuration}" \
    '{
      description: "terraform apply",
      strategy: "rolling",
      kind: "full_auto",
      step_percentage: 100,
      target_configuration: $target
    }')"
  cf_api POST "/accounts/${CF_ACCOUNT_ID}/containers/applications/${application_id}/rollouts" "${rollout}" > /dev/null
  echo "[INFO] Updated: ${application_id}"
}

destroy() {
  local application_id
  application_id="$(find_application_id)"
  if [[ -z "${application_id}" ]]; then
    echo "[INFO] Container application '${CF_APP_NAME}' does not exist; nothing to delete"
    return 0
  fi
  echo "[INFO] Deleting container application '${CF_APP_NAME}' (${application_id})"
  cf_api DELETE "/accounts/${CF_ACCOUNT_ID}/containers/applications/${application_id}" > /dev/null
}

case "${1:-}" in
  apply)   apply ;;
  destroy) destroy ;;
  *)       echo "Usage: $0 apply|destroy" >&2; exit 2 ;;
esac
