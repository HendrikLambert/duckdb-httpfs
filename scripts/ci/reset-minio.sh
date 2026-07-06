#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

# Re-seed MinIO between variants: force-recreating minio-setup re-runs its
# entrypoint (mc rb --force + rebuild), then refresh the changed presigned URLs.

docker compose -f scripts/ci/docker-compose.yml up -d --force-recreate --no-deps minio-setup >/dev/null
./scripts/ci/scrape-presigned.sh
