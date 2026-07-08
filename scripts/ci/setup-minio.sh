#!/usr/bin/env sh

MC=/usr/bin/mc
ALIAS=myminio
MINIO_URL=http://duckdb-minio.com:9000
ROOT_USER=duckdb_minio_admin
ROOT_PASSWORD=duckdb_minio_admin_password

until (
	"$MC" alias set "$ALIAS" "$MINIO_URL" "$ROOT_USER" "$ROOT_PASSWORD"
); do
	echo "...waiting..."
	sleep 1
done

"$MC" admin user add "$ALIAS" minio_duckdb_user minio_duckdb_user_password
"$MC" admin policy attach "$ALIAS" readwrite --user minio_duckdb_user

"$MC" admin user add "$ALIAS" minio_duckdb_user_2 minio_duckdb_user_2_password
"$MC" admin policy attach "$ALIAS" readwrite --user minio_duckdb_user_2

"$MC" rb --force "$ALIAS/test-bucket"
"$MC" mb "$ALIAS/test-bucket"
"$MC" version enable "$ALIAS/test-bucket"

"$MC" rb --force "$ALIAS/test-bucket-2"
"$MC" mb "$ALIAS/test-bucket-2"

"$MC" rb --force "$ALIAS/test-bucket-public"
"$MC" mb "$ALIAS/test-bucket-public"
"$MC" anonymous set public "$ALIAS/test-bucket-public"

if [ "${SEED_DUCKDB_DATA:-0}" = "1" ]; then
	"$MC" mirror /duckdb/data "$ALIAS/test-bucket/data"
fi

"$MC" cp /duckdb/data/csv/phonenumbers.csv "$ALIAS/test-bucket/presigned/phonenumbers.csv"
"$MC" cp /duckdb/data/parquet-testing/glob/t1.parquet "$ALIAS/test-bucket/presigned/t1.parquet"
"$MC" cp /duckdb/test_data/presigned-url-lineitem.parquet "$ALIAS/test-bucket/presigned/lineitem_large.parquet"
"$MC" cp /duckdb/test_data/attach.db "$ALIAS/test-bucket/presigned/attach.db"
"$MC" cp /duckdb/test_data/lineitem_sf1.db "$ALIAS/test-bucket/presigned/lineitem_sf1.db"

"$MC" share download "$ALIAS/test-bucket/presigned/phonenumbers.csv"
"$MC" share download "$ALIAS/test-bucket/presigned/t1.parquet"
"$MC" share download "$ALIAS/test-bucket/presigned/lineitem_large.parquet"
"$MC" share download "$ALIAS/test-bucket/presigned/attach.db"

echo "FINISHED SETTING UP MINIO"
exit 0
