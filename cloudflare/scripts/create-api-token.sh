#!/usr/bin/env bash
#
# Creates the user-owned API token Terraform needs and writes it to ./.env,
# in the three shapes Terraform reads it:
#
#   CLOUDFLARE_API_TOKEN   the token, for the Cloudflare provider and wrangler
#   AWS_ACCESS_KEY_ID      the token's ID, for the S3 backend talking to R2
#   AWS_SECRET_ACCESS_KEY  SHA-256 of the token, likewise
#
# R2's S3 API authenticates with an ordinary API token this way, so one token
# covers both the provider and the state bucket.
# https://developers.cloudflare.com/r2/api/tokens/
#
# Uses the cf CLI's OAuth login, which may create user tokens (account-owned
# tokens need a permission OAuth cannot grant). The token has nothing on the
# zone: the hostname and the zone's rules are applied from the egpl.dev
# repository.
#
# Usage: create-api-token.sh <account id> [bucket name] [token name]
#
# The token value is only printed to .env; the dashboard never shows it again.
set -euo pipefail

account_id="${1:?account id}"
bucket="${2:-terraform-state}"
name="${3:-ghcr-badge-terraform}"
env_file="$(dirname "$0")/../.env"

# Permission groups from GET /user/tokens/permission_groups.
account_groups=(
  e086da7e2179491d91ee5f35b3ca210a # Workers Scripts Write
  bdbcd690c763475a985e8641dddc09f7 # Workers Containers Write
)
bucket_groups=(
  2efd5506f9c8494dacb1fa10a3e7d5b6 # Workers R2 Storage Bucket Item Write (state)
)

groups_json() {
  printf '%s\n' "$@" | jq -R '{id: .}' | jq -s .
}

body="$(jq -n \
  --arg name "${name}" \
  --arg account "com.cloudflare.api.account.${account_id}" \
  --arg bucket "com.cloudflare.edge.r2.bucket.${account_id}_default_${bucket}" \
  --argjson account_groups "$(groups_json "${account_groups[@]}")" \
  --argjson bucket_groups "$(groups_json "${bucket_groups[@]}")" \
  '{
    name: $name,
    policies: [
      { effect: "allow", resources: { ($account): "*" }, permission_groups: $account_groups },
      { effect: "allow", resources: { ($bucket): "*" }, permission_groups: $bucket_groups }
    ]
  }')"

# cf must authenticate with its OAuth login, not an API token from .env.
result="$(env -u CLOUDFLARE_API_TOKEN cf user tokens create -q --body "${body}")"
token="$(jq -er '.value // .result.value' <<<"${result}")"
id="$(jq -r '.id // .result.id' <<<"${result}")"
secret="$(printf '%s' "${token}" | sha256sum | cut -d' ' -f1)"

# Replace the lines this script owns and keep any others.
umask 077
tmp="$(mktemp)"
if [[ -f "${env_file}" ]]; then
  grep -vE '^(CLOUDFLARE_API_TOKEN|AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY)=' "${env_file}" >"${tmp}" || true
fi
printf 'CLOUDFLARE_API_TOKEN=%s\nAWS_ACCESS_KEY_ID=%s\nAWS_SECRET_ACCESS_KEY=%s\n' \
  "${token}" "${id}" "${secret}" >>"${tmp}"
mv "${tmp}" "${env_file}"
echo "[INFO] Created API token \"${name}\" (id ${id}) and wrote it to ${env_file}" >&2
