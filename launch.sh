#!/usr/bin/env bash

set -euo pipefail

pip install . && ghcr-badge-server
