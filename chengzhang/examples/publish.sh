#!/bin/bash
# 与 Python 工具一致：bash examples/publish.sh check|prepare|preview|publish ...
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/publish.py" "$@"
