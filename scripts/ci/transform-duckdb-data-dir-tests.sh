#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

usage() {
  cat <<'EOF'
Usage: scripts/ci/transform-duckdb-data-dir-tests.sh [options]

Generate DuckDB SQLLogic tests with {DATA_DIR} rewritten for httpfs backends.

Options:
  --grep PATTERN       rg pattern, default: \{DATA_DIR\}
  --roots ROOTS        search roots, default: duckdb/test
  --file-globs GLOBS   rg -g globs, default: *.test *.test_slow
  --backends LIST      backends, default: http s3
  --list-only          only discover and write the test list
  -h, --help           show this help

Environment:
  GENERATED_TEST_ROOT       default: test/httpfs_logs/generated
  DISCOVERED_TESTS_FILE     default: test/httpfs_logs/duckdb-data-dir-tests.txt
  TRANSFORM_SUMMARY_FILE    default: test/httpfs_logs/duckdb-data-dir-transform.tsv
  RUN_ENV_FILE              default: test/httpfs_logs/duckdb-data-dir-run.env

Examples:
  scripts/ci/transform-duckdb-data-dir-tests.sh
  source test/httpfs_logs/duckdb-data-dir-run.env
  ./scripts/ci/run-ci-pipeline.sh

  scripts/ci/transform-duckdb-data-dir-tests.sh --backends http --grep 'TEMP_DIR|TEST_DIR'
EOF
}

TEST_GREP="${TEST_GREP:-\\{DATA_DIR\\}}"
SEARCH_ROOTS="${SEARCH_ROOTS:-duckdb/test}"
FILE_GLOBS="${FILE_GLOBS:-*.test *.test_slow}"
BACKENDS="${BACKENDS:-http s3}"
LIST_ONLY="${LIST_ONLY:-0}"
GENERATED_TEST_ROOT="${GENERATED_TEST_ROOT:-test/httpfs_logs/generated}"
DISCOVERED_TESTS_FILE="${DISCOVERED_TESTS_FILE:-test/httpfs_logs/duckdb-data-dir-tests.txt}"
TRANSFORM_SUMMARY_FILE="${TRANSFORM_SUMMARY_FILE:-test/httpfs_logs/duckdb-data-dir-transform.tsv}"
RUN_ENV_FILE="${RUN_ENV_FILE:-test/httpfs_logs/duckdb-data-dir-run.env}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --grep)
      TEST_GREP="$2"
      shift 2
      ;;
    --roots)
      SEARCH_ROOTS="$2"
      shift 2
      ;;
    --file-globs)
      FILE_GLOBS="$2"
      shift 2
      ;;
    --backends)
      BACKENDS="${2//,/ }"
      shift 2
      ;;
    --list-only)
      LIST_ONLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! command -v rg >/dev/null 2>&1; then
  echo "ERROR: rg is required to discover tests" >&2
  exit 1
fi

discover_tests() {
  local rg_args=(-l "$TEST_GREP")
  local glob root

  mkdir -p "$(dirname "$DISCOVERED_TESTS_FILE")"
  for glob in $FILE_GLOBS; do
    rg_args+=(-g "$glob")
  done
  for root in $SEARCH_ROOTS; do
    rg_args+=("$root")
  done

  rg "${rg_args[@]}" | sort > "$DISCOVERED_TESTS_FILE"
}

backend_data_dir() {
  local backend="$1"

  case "$backend" in
    http)
      printf '%s\n' "http://localhost:8008/data"
      ;;
    s3)
      printf '%s\n' "s3://test-bucket/data"
      ;;
    *)
      return 1
      ;;
  esac
}

generated_filter() {
  local test_file="$1"
  if [[ "$test_file" == duckdb/test/* ]]; then
    printf '%s' "${test_file#duckdb/}"
  else
    printf '%s' "$test_file"
  fi
}

generated_path() {
  local backend="$1"
  local test_file="$2"
  printf '%s/%s/%s' "$GENERATED_TEST_ROOT" "$backend" "$(generated_filter "$test_file")"
}

generate_backend_tests() {
  local backend="$1"
  local data_dir="$2"
  local root="$GENERATED_TEST_ROOT/$backend"
  local test_file target

  rm -rf "$root"
  while IFS= read -r test_file; do
    [[ -z "$test_file" ]] && continue
    target="$(generated_path "$backend" "$test_file")"
    mkdir -p "$(dirname "$target")"
    sed "s|{DATA_DIR}|$data_dir|g; s|\${DATA_DIR}|$data_dir|g" "$test_file" > "$target"
    printf '%s\t%s\t%s\n' "$backend" "$test_file" "$target" >> "$TRANSFORM_SUMMARY_FILE"
  done < "$DISCOVERED_TESTS_FILE"
}

backend_count=0
for backend in $BACKENDS; do
  backend_count=$((backend_count + 1))
done

if [[ $backend_count -eq 0 ]]; then
  echo "ERROR: no backends selected" >&2
  exit 1
fi

for backend in $BACKENDS; do
  data_dir="$(backend_data_dir "$backend" || true)"
  if [[ -z "$data_dir" || "$data_dir" == "null" ]]; then
    echo "ERROR: unknown backend '$backend' (supported: http, s3)" >&2
    exit 1
  fi
done

discover_tests
test_count="$(wc -l < "$DISCOVERED_TESTS_FILE" | tr -d ' ')"
echo "Discovered $test_count tests into $DISCOVERED_TESTS_FILE"
if [[ "$test_count" == "0" ]]; then
  echo "No tests matched grep pattern: $TEST_GREP" >&2
  exit 1
fi

if [[ "$LIST_ONLY" == "1" ]]; then
  exit 0
fi

mkdir -p "$(dirname "$TRANSFORM_SUMMARY_FILE")" "$(dirname "$RUN_ENV_FILE")"
printf 'backend\tsource\tgenerated\n' > "$TRANSFORM_SUMMARY_FILE"

for backend in $BACKENDS; do
  data_dir="$(backend_data_dir "$backend")"
  echo "Generating $backend tests with DATA_DIR=$data_dir"
  generate_backend_tests "$backend" "$data_dir"
done

test_filter="*$GENERATED_TEST_ROOT*"
if [[ $backend_count -eq 1 ]]; then
  for backend in $BACKENDS; do
    test_filter="*$GENERATED_TEST_ROOT/$backend*"
  done
fi

{
  echo "export TEST_FILTER='$test_filter'"
  echo "export HTTPFS_TEST_VARIANTS='${HTTPFS_TEST_VARIANTS:-curl}'"
  echo "export HTTPFS_IGNORE_TEST_FAILURES='${HTTPFS_IGNORE_TEST_FAILURES:-1}'"
  if [[ " $BACKENDS " == *" s3 "* ]]; then
    echo "export SEED_DUCKDB_DATA='${SEED_DUCKDB_DATA:-1}'"
  fi
} > "$RUN_ENV_FILE"

echo
echo "Generated tests under $GENERATED_TEST_ROOT"
echo "Transform summary: $TRANSFORM_SUMMARY_FILE"
echo "Run environment:   $RUN_ENV_FILE"
echo
echo "Next:"
echo "  source $RUN_ENV_FILE"
echo "  ./scripts/ci/run-ci-pipeline.sh"
