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

STATIC="[httpfs,parquet,json,core_functions]"
FILTER="${TEST_FILTER:-test/*}"

# $1 = on-init SQL ("" = default client); rest = optional command prefix.
run_suite() {
  local init="$1"; shift
  local args=("$FILTER" --skip-error-messages "[]")
  [[ -n "$init" ]] && args+=(--statically-loaded-extensions "$STATIC" --on-init "$init")
  "$@" "$UNITTEST" "${args[@]}"
}

reset_variant() {
  local name="$1"
  [[ "$name" == "default" ]] && return
  ./scripts/ci/reset-minio.sh
  source test/httpfs_logs/presigned.env
}

run_variant() {
  local name="$1"
  local gating="$2"
  local init="$3"
  shift 3

  reset_variant "$name"
  run_suite "$init" "$@"
  local rc=$?
  if [[ $rc -ne 0 && "$gating" == "1" && "${HTTPFS_IGNORE_TEST_FAILURES:-0}" != "1" ]]; then
    status=$rc
  fi
}

status=0
variants="${HTTPFS_TEST_VARIANTS:-default curl httplib caching}"
variants="${variants//,/ }"

for selected in $variants; do
  case "$selected" in
    default)
      run_variant default 1 ""
      ;;
    curl)
      run_variant curl 0 "SET httpfs_client_implementation='curl';"
      ;;
    httplib)
      run_variant httplib 0 "SET httpfs_client_implementation='httplib';" env -u HTTPFS_CONNECTION_CACHING_SUPPORTED
      ;;
    caching)
      run_variant caching 0 "SET httpfs_connection_caching=true;"
      ;;
    *)
      echo "ERROR: unknown HTTPFS_TEST_VARIANTS entry: $selected" >&2
      exit 1
      ;;
  esac
done

exit $status
