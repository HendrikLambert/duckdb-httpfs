#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

DATA_DIR=test/test_data
STORAGE_SQL=duckdb/test/sql/storage_version/generate_storage_version.sql
COMPOSE=(docker compose -f scripts/ci/docker-compose.yml --profile datagen)

force=0
[[ "${1:-}" == "--force" ]] && force=1

mkdir -p "$DATA_DIR"

datagen() { "${COMPOSE[@]}" run --rm -T datagen "$@"; }
missing() { [[ $force -eq 1 || ! -f "$DATA_DIR/$1" ]]; }

if missing presigned-url-lineitem.parquet; then
  echo ">> presigned-url-lineitem.parquet"
  datagen -c "INSTALL tpch; LOAD tpch; CALL dbgen(sf=1); COPY lineitem TO '/data/presigned-url-lineitem.parquet' (FORMAT parquet);"
fi

if missing lineitem_sf1.db; then
  echo ">> lineitem_sf1.db"
  rm -f "$DATA_DIR/lineitem_sf1.db"
  datagen /data/lineitem_sf1.db -c "INSTALL tpch; LOAD tpch; CALL dbgen(sf=1);"
fi

if missing attach.db; then
  echo ">> attach.db"
  rm -f "$DATA_DIR/attach.db"
  datagen /data/attach.db < "$STORAGE_SQL"
fi

echo "test data ready in $DATA_DIR"
