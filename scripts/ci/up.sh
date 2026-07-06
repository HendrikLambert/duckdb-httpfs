#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

COMPOSE=(docker compose -f scripts/ci/docker-compose.yml)
LOGS=test/httpfs_logs
ENV_FILE="$LOGS/presigned.env"

"${COMPOSE[@]}" down -v >/dev/null 2>&1 || true

rm -rf "$LOGS" /tmp/python_test_server
mkdir -p "$LOGS" /tmp/python_test_server
chmod 777 "$LOGS"

"${COMPOSE[@]}" up -d

echo "waiting for MinIO setup..."
./scripts/ci/scrape-presigned.sh

echo "stack up; presigned URLs -> $ENV_FILE"
