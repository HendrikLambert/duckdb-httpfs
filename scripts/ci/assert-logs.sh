#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

LOGS=test/httpfs_logs
chmod -R a+r "$LOGS" 2>/dev/null || true

docker run --rm \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  python:3.11-slim \
  python scripts/ci/log_assertions/run.py --logs "$LOGS"
