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

# $1 = on-init SQL ("" = default client); rest = optional command prefix.
run_suite() {
  local init="$1"; shift
  local args=("$FILTER" --skip-error-messages "[]")
  [[ -n "$init" ]] && args+=(--statically-loaded-extensions "$STATIC" --on-init "$init")
  "$@" "$UNITTEST" "${args[@]}"
}

# Non-gating variant; reset MinIO first.
variant() {
  ./scripts/ci/reset-minio.sh
  # shellcheck source=/dev/null
  source test/httpfs_logs/presigned.env
  run_suite "$@" || true
}

status=0
run_suite "" || status=$?

# httplib can't cache connections, so drop the flag to skip those tests.
variant "SET httpfs_client_implementation='curl';"
variant "SET httpfs_client_implementation='httplib';" env -u HTTPFS_CONNECTION_CACHING_SUPPORTED
variant "SET httpfs_connection_caching=true;"

exit $status
