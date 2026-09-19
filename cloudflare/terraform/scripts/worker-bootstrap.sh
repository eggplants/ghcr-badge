#!/usr/bin/env bash
#
# Creates the Durable Object class that backs the container, container-enabled.
# Driven by terraform_data in ../main.tf; see the comment there.
#
# A namespace only becomes container-enabled when the upload whose migration
# creates the class also lists the class under `containers`, and only the
# legacy script upload API (PUT /workers/scripts/{name}) honours that; the
# versions API the provider uses ignores it, and nothing can enable an
# existing namespace afterwards. So this uploads the bundle once through the
# legacy API with the migration and the container attachment, and the
# Terraform-managed version that follows only binds to the class. The upload
# also resets Worker settings it does not mention, so observability is sent
# to match cloudflare_worker.sparql.
#
# Usage: worker-bootstrap.sh
#
# Environment:
#   CLOUDFLARE_API_TOKEN   token with Workers Scripts:Edit
#   CF_ACCOUNT_ID          account that owns the Worker
#   CF_WORKER_NAME         Worker script name
#   CF_CLASS_NAME          Durable Object class to create
#   CF_BUNDLE              path to the Worker bundle (index.mjs)
#   CF_COMPATIBILITY_DATE  compatibility date of the Worker
set -euo pipefail

API="${CF_API_BASE:-https://api.cloudflare.com/client/v4}"
: "${CLOUDFLARE_API_TOKEN:?CLOUDFLARE_API_TOKEN is not set}"
: "${CF_ACCOUNT_ID:?CF_ACCOUNT_ID is not set}"
: "${CF_WORKER_NAME:?CF_WORKER_NAME is not set}"
: "${CF_CLASS_NAME:?CF_CLASS_NAME is not set}"
: "${CF_BUNDLE:?CF_BUNDLE is not set}"
: "${CF_COMPATIBILITY_DATE:?CF_COMPATIBILITY_DATE is not set}"

for cmd in curl jq; do
  command -v "${cmd}" > /dev/null || { echo "[ERROR] ${cmd} is required" >&2; exit 1; }
done

auth=(-sS -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}")
account="${API}/accounts/${CF_ACCOUNT_ID}"

# Idempotent: a namespace for the class means the migration already ran.
existing="$(curl "${auth[@]}" "${account}/workers/durable_objects/namespaces" |
  jq -r --arg script "${CF_WORKER_NAME}" --arg class "${CF_CLASS_NAME}" \
    '.result[] | select(.script == $script and .class == $class) | .id')"
if [[ -n "${existing}" ]]; then
  echo "[INFO] Durable Object namespace for ${CF_CLASS_NAME} already exists (${existing}); nothing to do"
  exit 0
fi

# Migration tags chain: continue from the script's current tag if it has one.
current_tag="$(curl "${auth[@]}" "${account}/workers/scripts" |
  jq -r --arg script "${CF_WORKER_NAME}" '.result[] | select(.id == $script) | .migration_tag // empty')"
if [[ -z "${current_tag}" ]]; then
  migrations="$(jq -nc --arg class "${CF_CLASS_NAME}" '{new_tag: "v1", new_sqlite_classes: [$class]}')"
elif [[ "${current_tag}" =~ ^v([0-9]+)$ ]]; then
  migrations="$(jq -nc --arg old "${current_tag}" --arg new "v$((BASH_REMATCH[1] + 1))" --arg class "${CF_CLASS_NAME}" \
    '{old_tag: $old, new_tag: $new, new_sqlite_classes: [$class]}')"
else
  migrations="$(jq -nc --arg old "${current_tag}" --arg new "${current_tag}-container" --arg class "${CF_CLASS_NAME}" \
    '{old_tag: $old, new_tag: $new, new_sqlite_classes: [$class]}')"
fi

metadata="$(jq -nc \
  --arg date "${CF_COMPATIBILITY_DATE}" \
  --arg class "${CF_CLASS_NAME}" \
  --argjson migrations "${migrations}" \
  '{
    main_module: "index.mjs",
    compatibility_date: $date,
    compatibility_flags: ["nodejs_compat"],
    migrations: $migrations,
    containers: [{class_name: $class}],
    bindings: [],
    observability: {enabled: true, head_sampling_rate: 1}
  }')"

echo "[INFO] Creating container-enabled Durable Object class ${CF_CLASS_NAME} on ${CF_WORKER_NAME} ($(jq -r '.new_tag' <<< "${migrations}"))"
response="$(curl "${auth[@]}" -X PUT "${account}/workers/scripts/${CF_WORKER_NAME}" \
  -F "metadata=${metadata};type=application/json" \
  -F "index.mjs=@${CF_BUNDLE};type=application/javascript+module")"
if [[ "$(jq -r '.success // false' <<< "${response}")" != "true" ]]; then
  echo "[ERROR] PUT /workers/scripts/${CF_WORKER_NAME} failed:" >&2
  jq -r '.errors // .' <<< "${response}" >&2
  exit 1
fi

namespace_id="$(curl "${auth[@]}" "${account}/workers/durable_objects/namespaces" |
  jq -r --arg script "${CF_WORKER_NAME}" --arg class "${CF_CLASS_NAME}" \
    '.result[] | select(.script == $script and .class == $class) | .id')"
echo "[INFO] Durable Object namespace: ${namespace_id:-not visible yet}"
