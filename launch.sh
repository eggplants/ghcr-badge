#!/usr/bin/env bash

set -euo pipefail

if ! command -v ghcr-badge-server &>/dev/null; then
  pip install .
fi
ghcr-badge-server
