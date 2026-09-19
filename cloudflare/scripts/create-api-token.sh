#!/usr/bin/env bash
#
# Creates the user-owned API token Terraform needs and writes it to ./.env as
# CLOUDFLARE_API_TOKEN. Uses the cf CLI's OAuth login, which may create user
# tokens (account-owned tokens need a permission OAuth cannot grant).
#
# Usage: create-api-token.sh <account id> <zone id> [token name]
#
# The token value is only printed to .env; the dashboard never shows it again.
set -euo pipefail

account_id="${1:?account id}"
zone_id="${2:?zone id}"
name="${3:-ghcr-badge-terraform}"
env_file="$(dirname "$0")/../.env"

# Permission groups from GET /user/tokens/permission_groups.
account_groups=(
  e086da7e2179491d91ee5f35b3ca210a # Workers Scripts Write
  bdbcd690c763475a985e8641dddc09f7 # Workers Containers Write
)
zone_groups=(
  c8fed203ed3043cba015a93ad1616f1f # Zone Read
  3030687196b94b638145a3953da2b699 # Zone Settings Write
  43137f8d07884d3198dc0ee77ca6e79b # Firewall Services Write
  fb6778dc191143babbfaa57993f1d275 # Zone WAF Write
  4755a26eedb94da69e1066d98aa820be # DNS Write
  28f4b596e7d643029c524985477ae49a # Workers Routes Write
)

groups_json() {
  printf '%s\n' "$@" | jq -R '{id: .}' | jq -s .
}

body="$(jq -n \
  --arg name "${name}" \
  --arg account "com.cloudflare.api.account.${account_id}" \
  --arg zone "com.cloudflare.api.account.zone.${zone_id}" \
  --argjson account_groups "$(groups_json "${account_groups[@]}")" \
  --argjson zone_groups "$(groups_json "${zone_groups[@]}")" \
  '{
    name: $name,
    policies: [
      { effect: "allow", resources: { ($account): "*" }, permission_groups: $account_groups },
      { effect: "allow", resources: { ($zone): "*" }, permission_groups: $zone_groups }
    ]
  }')"

# cf must authenticate with its OAuth login, not an API token from .env.
result="$(env -u CLOUDFLARE_API_TOKEN cf user tokens create -q --body "${body}")"
token="$(jq -er '.value // .result.value' <<<"${result}")"
id="$(jq -r '.id // .result.id' <<<"${result}")"

umask 077
printf 'CLOUDFLARE_API_TOKEN=%s\n' "${token}" >"${env_file}"
echo "[INFO] Created API token \"${name}\" (id ${id}) and wrote it to ${env_file}" >&2
