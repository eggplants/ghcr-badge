---
app_name: "ghcr-badge"
title: "ghcr-badge"
tagline: "Generate ghcr.io (GitHub Container Registory) container status badge"
theme_color: "#44cc11"
git: "https://github.com/eggplants/ghcr-badge"
homepage: "https://ghcr-badge.egpl.dev"
---

## Motivation

<https://github.com/badges/shields/issues/5594>

## Deployment

- <https://ghcr-badge.egpl.dev/>
- <https://ghcr-badge.deta.dev/>

## Available paths

- `/<package_owner>/<package_name>/tags?color=...&ignore=...&n=...&label=...&trim=...`
  - defaults: `color=#44cc11`, `ignore=latest`, `n=3`, `label=image tags`
  - <https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/tags?trim=major>
- `/<package_owner>/<package_name>/latest_tag?color=...&ignore=...&label=...&trim=...`
  - defaults: `color=#44cc11`, `ignore=latest`, `label=version`
  - <https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/latest_tag?trim=major&label=latest>
- `/<package_owner>/<package_name>/size?color=...&tag=...&label=...&trim=...`
  - defaults: `color=#44cc11`, `tag=latest`, `label=image size`
  - <https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/size>

## Common parameters

### `label` parameter

- `label=hello`

### `ignore` parameter

Use the ignore parameter to filter returned tags, supports pattern matching and a comma separated list.

- `ignore=latest` ignores the `latest` tag (default).
- `ignore=sha256*` ignores all tags prefixed with `sha256`.
- `ignore=v0.0.1,latest,sha256*` ignores the `latest` and `v0.0.1` tags, and all tags prefixed with `sha256*`.

### `trim` parameter

- `trim=patch` trims `^v?\d+\.\d+\.\d+[^.]*$` tags.
- `trim=major` trims `^v?\d+\.\d+[^.]*$` tags.

### `color` parameter

Available color names and hex codes are listed on [here](https://github.com/jongracecox/anybadge#colors).

## Note

Generated badge will be cached for 3666 seconds in GitHub's [Camo](https://github.com/atmos/camo) server.
To update immediately, send PURGE request to the badge Camo link.

```bash
curl -X PURGE "https://camo.githubusercontent.com/..."
```
