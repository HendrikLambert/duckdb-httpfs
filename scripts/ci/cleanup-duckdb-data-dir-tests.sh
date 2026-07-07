#!/usr/bin/env sh

if [ ! -d scripts/ci ] || [ ! -d test/httpfs_logs ]; then
  script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd)
  cd "$script_dir/../.." || exit 1
fi

GENERATED_TEST_ROOT="${GENERATED_TEST_ROOT:-test/httpfs_logs/generated}"
DISCOVERED_TESTS_FILE="${DISCOVERED_TESTS_FILE:-test/httpfs_logs/duckdb-data-dir-tests.txt}"
TRANSFORM_SUMMARY_FILE="${TRANSFORM_SUMMARY_FILE:-test/httpfs_logs/duckdb-data-dir-transform.tsv}"
RUN_ENV_FILE="${RUN_ENV_FILE:-test/httpfs_logs/duckdb-data-dir-run.env}"
RUN_SUMMARY_FILE="${RUN_SUMMARY_FILE:-test/httpfs_logs/duckdb-data-dir-summary.tsv}"

rm -rf "$GENERATED_TEST_ROOT"
rm -f "$DISCOVERED_TESTS_FILE" "$TRANSFORM_SUMMARY_FILE" "$RUN_ENV_FILE" "$RUN_SUMMARY_FILE"

unset TEST_FILTER
unset HTTPFS_TEST_VARIANTS
unset HTTPFS_IGNORE_TEST_FAILURES
unset SEED_DUCKDB_DATA

echo "Cleaned generated DuckDB DATA_DIR tests and run env files."

if ! (return 0 2>/dev/null); then
  echo "Note: run with 'source scripts/ci/cleanup-duckdb-data-dir-tests.sh' to also unset variables in your current shell."
fi
