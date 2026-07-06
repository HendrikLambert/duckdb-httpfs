#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/../.."

source scripts/ci/set-ci-env.sh
# shellcheck source=/dev/null
source test/httpfs_logs/presigned.env

UNITTEST=build/release/test/unittest
for cfg in release reldebug debug; do
  if [[ -x "build/$cfg/test/unittest" ]]; then UNITTEST="build/$cfg/test/unittest"; break; fi
done
if [[ ! -x "$UNITTEST" ]]; then
  echo "ERROR: no unittest binary found (run 'make' first)" >&2
  exit 1
fi

STATIC="[httpfs,parquet,core_functions]"
FILTER="${TEST_FILTER:-test/*}"
status=0

# Gating run (default client).
"$UNITTEST" "$FILTER" --skip-error-messages "[]" || status=$?

# Non-gating variants: exercise each client so the UA assertion covers them;
# reset MinIO first for clean state + refreshed presigned URLs.
for init in \
  "SET httpfs_client_implementation='curl';" \
  "SET httpfs_client_implementation='httplib';" \
  "SET httpfs_connection_caching=true;"
do
  ./scripts/ci/reset-minio.sh
  # shellcheck source=/dev/null
  source test/httpfs_logs/presigned.env
  "$UNITTEST" "$FILTER" --skip-error-messages "[]" --statically-loaded-extensions "$STATIC" --on-init "$init" || true
done

exit $status
