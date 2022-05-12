# ghcr-badge: Generate ghcr.io container's status badge

[![Heroku App Status](http://heroku-shields.herokuapp.com/ghcr-badge)](https://ghcr-badge.herokuapp.com)

**🖕If the status badge is not shown correctly, please click to wake up hibernated server.**

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

## DEMO

- `/<string:package_owner>/<string:package_name>/tags?color=...`
  - <https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/tags>
  - 👉: ![1](https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/tags)
- `/<string:package_owner>/<string:package_name>/latest_tag?color=...`
  - <https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/latest_tag>
  - 👉: ![2](https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/latest_tag)
- `/<string:package_owner>/<string:package_name>/size?tag=...&color=...`
  - <https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/size?tag=latest>
  - 👉: ![3](https://ghcr-badge.herokuapp.com/eggplants/ghcr-badge/size?tag=latest)
