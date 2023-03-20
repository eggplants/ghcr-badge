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

- <https://ghcr-badge.deta.dev/>
  - [![Website](https://img.shields.io/website?label=deta.dev&url=https%3A%2F%2Fghcr-badge.deta.dev)](https://ghcr-badge.deta.dev)

## Available paths

- `/<string:package_owner>/<string:package_name>/tags?color=...&ignore=...&n=...&label=...&trim=...`
  - defaults: `color=#e05d44`, `ignore=latest`, `n=3`, `label=image tags`
  - <https://ghcr-badge.deta.dev/eggplants/ghcr-badge/tags?trim=major>
  - 👉: ![1]
- `/<string:package_owner>/<string:package_name>/latest_tag?color=...&ignore=...&label=...&trim=...`
  - defaults: `color=#e05d44`, `ignore=latest`, `label=version`
  - <https://ghcr-badge.deta.dev/eggplants/ghcr-badge/latest_tag?trim=major&label=latest>
  - 👉: ![2]
- `/<string:package_owner>/<string:package_name>/develop_tag?color=...&label=...`
  - defaults: `color=#e05d44`, `label=develop`
  - <https://ghcr-badge.deta.dev/ptr727/plexcleaner/develop_tag>
  - 👉: ![3]
- `/<string:package_owner>/<string:package_name>/size?color=...&tag=...&label=...&trim=...`
  - defaults: `color=#e05d44`, `tag=latest`, `label=image size`
  - <https://ghcr-badge.deta.dev/eggplants/ghcr-badge/size>
  - 👉: ![4]

## Common parameters

### `label` parameter

- `label=hello`: ![label=hello](https://ghcr-badge.deta.dev/eggplants/ghcr-badge/tags?trim=major&label=hello)

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

GitHub caches badge data in 604800 seconds(=7 days).

The server will send headers to prevent this and set the cache time to 3666 seconds ,
to have purge the cache before, try: `curl -X PURGE "https://camo.githubusercontent.com/..."` (it's badge image link)
in the `server.py` is documented what leads to "no-caching" at all with github camo cache

[1]: <https://ghcr-badge.deta.dev/eggplants/ghcr-badge/tags?trim=major>
[2]: <https://ghcr-badge.deta.dev/eggplants/ghcr-badge/latest_tag?trim=major&label=latest>
[3]: <https://ghcr-badge.deta.dev/ptr727/plexcleaner/develop_tag>
[4]: <https://ghcr-badge.deta.dev/eggplants/ghcr-badge/size>
