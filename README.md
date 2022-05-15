# ghcr-badge: Generate ghcr.io container's status badge

[![PyPI version](https://badge.fury.io/py/ghcr-badge.svg)](https://badge.fury.io/py/ghcr-badge) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/eggplants/ghcr-badge/master.svg)](https://results.pre-commit.ci/latest/github/eggplants/ghcr-badge/master) [![Maintainability](https://api.codeclimate.com/v1/badges/f77401f6fb543dd8c436/maintainability)](https://codeclimate.com/github/eggplants/ghcr-badge/maintainability) [![Release Package](https://github.com/eggplants/ghcr-badge/actions/workflows/release.yml/badge.svg)](https://github.com/eggplants/ghcr-badge/actions/workflows/release.yml)

## Motivation

<https://github.com/badges/shields/issues/5594>

## Deployment

- <https://ghcr-badge.herokuapp.com/>
  - [![Heroku App Status](http://heroku-shields.herokuapp.com/ghcr-badge)](https://ghcr-badge.herokuapp.com)
  - **🖕If this status badge is not shown correctly, please click to wake up hibernated server.**

## DEMO

- `/<string:package_owner>/<string:package_name>/tags?color=...&ignore=...&n=...&label=...`
  - defaults: `color=#e05d44`, `ignore=latest`, `n=3`
  - <https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/tags?ignore=latest,0.0>
  - 👉: ![1](https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/tags?ignore=latest,0.0)
- `/<string:package_owner>/<string:package_name>/latest_tag?color=...&ignore=...&label=...`
  - defaults: `color=#e05d44`, `ignore=latest`
  - <https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/latest_tag>
  - 👉: ![2](https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/latest_tag)
- `/<string:package_owner>/<string:package_name>/size?color=...&tag=...&label=...`
  - defaults: `color=#e05d44`, `tag=latest`
  - <https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/size>
  - 👉: ![3](https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/size)

## Note

GitHub caches badge data in 604800 seconds(=7 days). To update, try: `curl -X PURGE "https://camo.githubusercontent.com/..."` (it's badge image link)
