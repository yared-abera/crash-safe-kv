#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${APP_DIR}/kvstore"
cp "${SCRIPT_DIR}/kvstore_store.py" "${APP_DIR}/kvstore/store.py"
