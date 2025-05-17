# ghcr-badge: Generate ghcr.io container's status badge

[![1] ![2] ![3]](https://github.com/eggplants/ghcr-badge/pkgs/container/ghcr-badge)

[![PyPI version](
  <https://badge.fury.io/py/ghcr-badge.svg>
  )](
  <https://badge.fury.io/py/ghcr-badge>
) [![pre-commit.ci status](
  <https://results.pre-commit.ci/badge/github/eggplants/ghcr-badge/master.svg>
  )](
  <https://results.pre-commit.ci/latest/github/eggplants/ghcr-badge/master>
) [![Maintainability](
  <https://qlty.sh/badges/e53a09a0-bc44-44d9-a974-77c40c5d0387/maintainability.svg>
  )](
  <https://qlty.sh/gh/eggplants/projects/ghcr-badge>
  ) [![Release Package](
  <https://github.com/eggplants/ghcr-badge/actions/workflows/release.yml/badge.svg>
  )](
  <https://github.com/eggplants/ghcr-badge/actions/workflows/release.yml>
)

## Motivation

<https://github.com/badges/shields/issues/5594>

## Deployment

[![Deploy to Render]](https://render.com/deploy?repo=https://github.com/eggplants/ghcr-badge)

- <https://ghcr-badge.egpl.dev/>
  - [![Website](https://img.shields.io/website?label=egpl.dev&url=https%3A%2F%2Fghcr-badge.egpl.dev)](https://ghcr-badge.egpl.dev)

- ~<https://ghcr-badge.deta.dev/>~
  - Deta Space was [closed](https://deta.space/sunset)

[Deploy to Render]: <https://render.com/images/deploy-to-render-button.svg>

## Available paths

- `/<package_owner>/<package_name>/tags?color=...&ignore=...&n=...&label=...&trim=...`
  - defaults: `color=#44cc11`, `ignore=latest`, `n=3`, `label=image tags`
  - <https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/tags?trim=major>
  - 👉: ![1]
- `/<package_owner>/<package_name>/latest_tag?color=...&ignore=...&label=...&trim=...`
  - defaults: `color=#44cc11`, `ignore=latest`, `label=version`
  - <https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/latest_tag?trim=major&label=latest>
  - 👉: ![2]
- `/<package_owner>/<package_name>/size?color=...&tag=...&label=...&trim=...`
  - defaults: `color=#44cc11`, `tag=latest`, `label=image size`
  - <https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/size>
  - 👉: ![3]

## Common parameters

### `label` parameter

- `label=hello`: ![label=hello](https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/tags?trim=major&label=hello)

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

[1]: <https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/tags?trim=major>
[2]: <https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/latest_tag?trim=major&label=latest>
[3]: <https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/size>

## Development

1. Install [`poetry`](https://python-poetry.org/docs/#installation)
1. Run `poetry install && poetry shell && pre-commit install`
1. Launch live server with `task dev`
