#!/usr/bin/env bash
#
# Prints the Cloudflare token mise.toml exports as CLOUDFLARE_API_TOKEN for
# wrangler and Terraform.
#
# An API token already present in CLOUDFLARE_API_TOKEN (from .env, see
# README) is passed through untouched. Otherwise the OAuth token the cf CLI
# stored with `cf auth login` is used, refreshed first if it has expired. cf
# OAuth tokens start with "cfoat_", which is how the two are told apart; the
# variable may already hold one of ours when mise re-evaluates its env.
#
# The OAuth token only lives for an hour, so long task chains (build + push +
# apply) must call this right before each command that talks to the API
# instead of relying on a value captured when the chain started. cf refreshes
# its stored token only when CLOUDFLARE_API_TOKEN is unset and the token has
# already expired, so the variable is cleared for that call.
set -euo pipefail

if [[ -n "${CLOUDFLARE_API_TOKEN:-}" && "${CLOUDFLARE_API_TOKEN}" != cfoat_* ]]; then
  printf '%s\n' "${CLOUDFLARE_API_TOKEN}"
  exit 0
fi

config="${XDG_CONFIG_HOME:-${HOME}/.config}/cloudflare/config/default.json"
if [[ ! -f "${config}" ]]; then
  echo "[ERROR] No cf credentials at ${config}. Run: cf auth login" >&2
  exit 1
fi

expired="$(jq -r '
  (.expiration_time // "1970-01-01T00:00:00Z")
  | sub("\\.[0-9]+Z$"; "Z") | fromdateiso8601 <= now
' "${config}")"

if [[ "${expired}" == "true" ]]; then
  echo "[INFO] Cloudflare OAuth token expired; refreshing" >&2
  whoami_json="$(env -u CLOUDFLARE_API_TOKEN cf auth whoami -q)"
  if [[ "$(jq -r '.tokenValid // false' <<<"${whoami_json}")" != "true" ]]; then
    echo "[ERROR] Could not refresh the Cloudflare OAuth token. Run: cf auth login" >&2
    exit 1
  fi
fi

jq -er '.oauth_token // empty' "${config}"
