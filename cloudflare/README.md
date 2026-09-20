# ghcr-badge on Cloudflare Containers

## Requirements

- A Cloudflare account on the Workers Paid plan
- The zone the badges are served from (`egpl.dev`), managed in the [iac](https://github.com/eggplants/iac) repository
- [mise](https://mise.jdx.dev/), Docker, `curl`, `jq`

## Setup

```bash
cd cloudflare
mise trust
cf auth login

# writes CLOUDFLARE_API_TOKEN to .env
scripts/create-api-token.sh <account id> <zone id>   

cp terraform/terraform.tfvars.example terraform/terraform.tfvars

# account_id, hostname
$EDITOR terraform/terraform.tfvars

mise run init
```

## Deploy

```bash
# pull ghcr.io/eggplants/ghcr-badge:<latest tag>
# push it to the Cloudflare registry, terraform apply
mise run deploy
APP_VERSION=2.0.0 mise run deploy

# check
curl -sSI 'https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/tags?trim=major' | grep -i x-cache
```

| Task | Command |
| --- | --- |
| Lint and test | `mise run lint` |
| Preview changes | `mise run plan` |
| Change a rate limit, TTL or `sleep_after` | edit `terraform.tfvars`, then `terraform -chdir=terraform apply -replace=cloudflare_worker_version.badge` |
| Tear down | `mise run destroy && wrangler containers images delete` |
