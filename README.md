# ghcr-badge: Generate ghcr.io container's status badge

[![1] ![2] ![4]](https://github.com/eggplants/ghcr-badge/pkgs/container/ghcr-badge)

[![PyPI version](
  https://badge.fury.io/py/ghcr-badge.svg
  )](
  https://badge.fury.io/py/ghcr-badge
) [![pre-commit.ci status](
  https://results.pre-commit.ci/badge/github/eggplants/ghcr-badge/master.svg
  )](
  https://results.pre-commit.ci/latest/github/eggplants/ghcr-badge/master
) [![Maintainability](
  https://api.codeclimate.com/v1/badges/f77401f6fb543dd8c436/maintainability
  )](
  https://codeclimate.com/github/eggplants/ghcr-badge/maintainability
) [![Release Package](
  https://github.com/eggplants/ghcr-badge/actions/workflows/release.yml/badge.svg
  )](
  https://github.com/eggplants/ghcr-badge/actions/workflows/release.yml
)

## Motivation

<https://github.com/badges/shields/issues/5594>

## Deployment

- <https://ghcr-badge.herokuapp.com/>
  - [![Heroku App Status](http://heroku-shields.herokuapp.com/ghcr-badge)](https://ghcr-badge.herokuapp.com)
  - **🖕If this status badge is not shown correctly, please click to wake up hibernated server.**

## Available paths

- `/<string:package_owner>/<string:package_name>/tags?color=...&ignore=...&n=...&label=...&trim=...`
  - defaults: `color=#e05d44`, `ignore=latest`, `n=3`, `label=image tags`
  - <https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/tags?trim=major>
  - 👉: ![1]
- `/<string:package_owner>/<string:package_name>/latest_tag?color=...&ignore=...&label=...&trim=...`
  - defaults: `color=#e05d44`, `ignore=latest`, `label=version`
  - <https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/latest_tag?trim=major>
  - 👉: ![2]
- `/<string:package_owner>/<string:package_name>/develop_tag?color=...&label=...`
  - defaults: `color=#e05d44`, `label=develop`
  - <https://ghcr-badge.herokuapp.com/ptr727/plexcleaner/develop_tag>
  - 👉: ![3]
- `/<string:package_owner>/<string:package_name>/size?color=...&tag=...&label=...&trim=...`
  - defaults: `color=#e05d44`, `tag=latest`, `label=image size`
  - <https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/size>
  - 👉: ![4]

## Common parameters

### `label` parameter

- `label=🤔`: ![label=🤔](https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/tags?trim=major&label=🤔)

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

GitHub caches badge data in 604800 seconds(=7 days). To update, try: `curl -X PURGE "https://camo.githubusercontent.com/..."` (it's badge image link)

[1]: https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/tags?trim=major
[2]: https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/latest_tag?trim=major
[3]: https://ghcr-badge.herokuapp.com/ptr727/plexcleaner/develop_tag
[4]: https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/size
