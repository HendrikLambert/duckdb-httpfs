#!/usr/bin/env bash
# Static test env; dynamic presigned URLs live in presigned.env.

export S3_TEST_SERVER_AVAILABLE=1
export AWS_DEFAULT_REGION=eu-west-1
export AWS_ACCESS_KEY_ID=minio_duckdb_user
export AWS_SECRET_ACCESS_KEY=minio_duckdb_user_password
export DUCKDB_S3_ENDPOINT=duckdb-minio.com:9000
export DUCKDB_S3_USE_SSL=false
export HTTP_PROXY_PUBLIC=localhost:3128
export TEST_PERSISTENT_SECRETS_AVAILABLE=true
export S3_ATTACH_DB=s3://test-bucket/presigned/attach.db
export PYTHON_HTTP_SERVER_URL=http://localhost:8008
export PYTHON_HTTP_SERVER_DIR=/tmp/python_test_server
# Gates the connection-caching tests; run-tests.sh drops it for the httplib variant.
export HTTPFS_CONNECTION_CACHING_SUPPORTED=1
