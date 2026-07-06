#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/../.."

teardown() {
  if [[ "${KEEP_UP:-0}" == "1" ]]; then
    echo "KEEP_UP=1: leaving the stack running"
    return
  fi
  docker compose -f scripts/ci/docker-compose.yml down -v >/dev/null 2>&1 || true
}
trap teardown EXIT

./scripts/ci/generate-data.sh || exit 1
./scripts/ci/up.sh || exit 1

tests_status=0
./scripts/ci/run-tests.sh || tests_status=$?

assert_status=0
./scripts/ci/assert-logs.sh || assert_status=$?

echo
echo "==== pipeline summary ===="
echo "tests:      $([[ $tests_status -eq 0 ]] && echo PASS || echo FAIL)"
echo "ua-logs:    $([[ $assert_status -eq 0 ]] && echo PASS || echo FAIL)"

[[ $tests_status -eq 0 && $assert_status -eq 0 ]]
