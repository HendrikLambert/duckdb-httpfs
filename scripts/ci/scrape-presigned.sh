#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

# Wait for minio-setup to finish, then write its presigned URLs to presigned.env.

COMPOSE=(docker compose -f scripts/ci/docker-compose.yml)
ENV_FILE=test/httpfs_logs/presigned.env

for i in $(seq 1 120); do
  "${COMPOSE[@]}" logs minio-setup 2>/dev/null | grep -q 'FINISHED SETTING UP MINIO' && break
  if [[ $i -eq 120 ]]; then
    echo "ERROR: MinIO setup did not finish" >&2
    "${COMPOSE[@]}" logs minio-setup >&2
    exit 1
  fi
  sleep 1
done

logs=$("${COMPOSE[@]}" logs minio-setup 2>/dev/null)
share() { grep -m1 "Share:.*$1" <<<"$logs" | grep -o 'http[s]\?://[^ ]\+'; }

{
  echo "export S3_SMALL_CSV_PRESIGNED_URL='$(share 'phonenumbers\.csv')'"
  echo "export S3_SMALL_PARQUET_PRESIGNED_URL='$(share 't1\.parquet')'"
  echo "export S3_LARGE_PARQUET_PRESIGNED_URL='$(share 'lineitem_large\.parquet')'"
  echo "export S3_ATTACH_DB_PRESIGNED_URL='$(share 'attach\.db')'"
} > "$ENV_FILE"
