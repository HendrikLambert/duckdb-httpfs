#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

COMPOSE=(docker compose -f scripts/ci/docker-compose.yml)
LOGS=test/httpfs_logs
ENV_FILE="$LOGS/presigned.env"

"${COMPOSE[@]}" down -v >/dev/null 2>&1 || true

mkdir -p "$LOGS" /tmp/python_test_server
chmod 777 "$LOGS"
rm -f "$ENV_FILE" "$LOGS"/squid-access.log "$LOGS"/http-access.log "$LOGS"/minio-trace.jsonl

# Pre-create the log files world-writable so the container writers (squid runs as
# an unprivileged uid) leave them host-readable for assert-logs.sh.
touch "$LOGS"/squid-access.log "$LOGS"/http-access.log "$LOGS"/minio-trace.jsonl
chmod 666 "$LOGS"/squid-access.log "$LOGS"/http-access.log "$LOGS"/minio-trace.jsonl

"${COMPOSE[@]}" up -d

echo "waiting for MinIO setup..."
./scripts/ci/scrape-presigned.sh

echo "stack up; presigned URLs -> $ENV_FILE"
