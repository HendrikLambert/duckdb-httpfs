#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

# One-time host setup (sudo, idempotent): MinIO /etc/hosts aliases so the host-run
# unittest resolves the S3 endpoints, and test secrets at 0700 (duckdb requires it).

for host in \
  duckdb-minio.com \
  test-bucket.duckdb-minio.com \
  test-bucket-2.duckdb-minio.com \
  test-bucket-public.duckdb-minio.com
do
  if ! grep -qE "^127\.0\.0\.1[[:space:]]+${host}([[:space:]]|$)" /etc/hosts; then
    echo "127.0.0.1 ${host}" >> /etc/hosts
  fi
done

chmod -R 700 data/secrets
