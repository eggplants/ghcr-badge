# ghcr-badge: Generate ghcr.io container's status badge

[![1] ![2] ![4]](https://github.com/eggplants/ghcr-badge/pkgs/container/ghcr-badge)

[![PyPI version](
  <https://badge.fury.io/py/ghcr-badge.svg>
  )](
  <https://badge.fury.io/py/ghcr-badge>
) [![pre-commit.ci status](
  <https://results.pre-commit.ci/badge/github/eggplants/ghcr-badge/master.svg>
  )](
  <https://results.pre-commit.ci/latest/github/eggplants/ghcr-badge/master>
) [![Maintainability](
  <https://api.codeclimate.com/v1/badges/f77401f6fb543dd8c436/maintainability>
  )](
  <https://codeclimate.com/github/eggplants/ghcr-badge/maintainability>
) [![Release Package](
  <https://github.com/eggplants/ghcr-badge/actions/workflows/release.yml/badge.svg>
  )](
  <https://github.com/eggplants/ghcr-badge/actions/workflows/release.yml>
)

## Motivation

<https://github.com/badges/shields/issues/5594>

## Deployment

[![Deploying on Deta Space](
  <https://img.shields.io/badge/deploying%20on-Deta%20Space-F26DAA>
  )](
  <https://deta.space/discovery/@eggplants/ghcrbadge>
)

- <https://ghcr-badge.egpl.dev/>
  - [![Website](https://img.shields.io/website?label=egpl.dev&url=https%3A%2F%2Fghcr-badge.egpl.dev)](https://ghcr-badge.egpl.dev)

- <https://ghcr-badge.deta.dev/>
  - [![Website](https://img.shields.io/website?label=deta.dev&url=https%3A%2F%2Fghcr-badge.deta.dev)](https://ghcr-badge.deta.dev)

## Available paths

- `/<package_owner>/<package_name>/tags?color=...&ignore=...&n=...&label=...&trim=...`
  - defaults: `color=#44cc11`, `ignore=latest`, `n=3`, `label=image tags`
  - <https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/tags?trim=major>
  - 👉: ![1]
- `/<package_owner>/<package_name>/latest_tag?color=...&ignore=...&label=...&trim=...`
  - defaults: `color=#44cc11`, `ignore=latest`, `label=version`
  - <https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/latest_tag?trim=major&label=latest>
  - 👉: ![2]
- `/<package_owner>/<package_name>/develop_tag?color=...&label=...`
  - defaults: `color=#44cc11`, `label=develop`
  - <https://ghcr-badge.egpl.dev/ptr727/plexcleaner/develop_tag>
  - 👉: ![3]
- `/<package_owner>/<package_name>/size?color=...&tag=...&label=...&trim=...`
  - defaults: `color=#44cc11`, `tag=latest`, `label=image size`
  - <https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/size>
  - 👉: ![4]

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
[3]: <https://ghcr-badge.egpl.dev/ptr727/plexcleaner/develop_tag>
[4]: <https://ghcr-badge.egpl.dev/eggplants/ghcr-badge/size>

## Development

1. Install [`poetry`](https://python-poetry.org/docs/#installation)
1. Run `poetry install && poetry shell && pre-commit install`
1. Launch live server with `task dev`
