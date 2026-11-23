# ghcr-badge on Cloudflare Containers

This Terraform manages only what lives in the account: the Worker, its Durable Object class, version, deployment and container. The hostname `ghcr-badge.egpl.dev` is attached to the Worker from [eggplants/egpl.dev](https://github.com/eggplants/egpl.dev) (`terraform/workers.tf`), which owns the `egpl.dev` zone. The state lives in that repository's R2 bucket, under `ghcr-badge/terraform.tfstate`.

## Requirements

- A Cloudflare account on the Workers Paid plan
- The R2 bucket `terraform-state`, made by `scripts/create-state-bucket.sh` in the egpl.dev repository
- [mise](https://mise.jdx.dev/), Docker, `curl`, `jq`

## Setup

```bash
cd cloudflare
mise trust
cf auth login

# writes CLOUDFLARE_API_TOKEN and the R2 credentials to .env
scripts/create-api-token.sh <account id>

cp terraform/terraform.tfvars.example terraform/terraform.tfvars

# account_id
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

When setting up from scratch, attach the hostname from the egpl.dev repository after the first deploy.

| Task | Command |
| --- | --- |
| Lint and test | `mise run lint` |
| Preview changes | `mise run plan` |
| Change a rate limit, TTL or `sleep_after` | edit `terraform.tfvars`, then `terraform -chdir=terraform apply -replace=cloudflare_worker_version.badge` |
| Tear down | detach the hostname in the egpl.dev repository, then `mise run destroy && wrangler containers images delete` |
