#!/usr/bin/env bash

# Print the absolute Fireworks root, installing the pinned backend when missing.

set -euo pipefail

script_dir="$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
exec python3 "${script_dir}/ensure_fireworks.py" "$@"
