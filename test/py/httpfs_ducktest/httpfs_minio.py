import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from ducktest import find_duckdb, get_context, sql_literal, use_service
from ducktest.workspace import scratch
from ducktest.resources.minio import (
    minio_anonymous_set,
    minio_env,
    minio_policy_attach,
    minio_presigned_url,
    minio_rclone,
    minio_service,
    minio_user_add,
    minio_version_enable,
)
from ducktest.tools.rclone import mkdir, sync

from .remote_data import prepare_remote_data

PUBLIC_BUCKET = "test-bucket-public"
SECONDARY_BUCKET = "test-bucket-2"
SECONDARY_USER = "minio_duckdb_user_2"
SECONDARY_PASSWORD = "minio_duckdb_user_2_password"

PRIMARY_USER = "minio_duckdb_user"
PRIMARY_PASSWORD = "minio_duckdb_user_password"
REGION = "eu-west-1"
PRIMARY_BUCKET = "test-bucket"
MINIO_DOMAIN = "127.0.0.1.nip.io"

_PRESIGNED_PREFIX = "presigned"
_SMALL_CSV = "phonenumbers.csv"
_SMALL_PARQUET = "t1.parquet"
_ATTACH_DB = "attach.db"


def httpfs_minio_env(block):
    env = minio_env(block)
    env.update({
        "S3_TEST_SERVER_AVAILABLE": "1",
        "AWS_DEFAULT_REGION": block["region"],
        "AWS_ACCESS_KEY_ID": block["access_key"],
        "AWS_SECRET_ACCESS_KEY": block["secret_key"],
        "DUCKDB_S3_ENDPOINT": block["s3_endpoint"],
        "DUCKDB_S3_USE_SSL": "false",
    })
    env.update(block.get("httpfs_env", {}))
    return env


def _generate_attach_database(config, destination):
    working_dir = Path(get_context(config).working_dir)
    source = working_dir / "duckdb/test/sql/storage_version/generate_storage_version.sql"
    duckdb = Path(find_duckdb(config, str(working_dir)))

    if destination.exists() and destination.stat().st_mtime_ns >= max(
        source.stat().st_mtime_ns,
        duckdb.stat().st_mtime_ns,
    ):
        return

    with tempfile.TemporaryDirectory(prefix="attach-", dir=destination.parent) as tmp:
        generated = Path(tmp) / destination.name
        sql = (
            f"ATTACH {sql_literal(str(generated))} AS db (STORAGE_VERSION 'latest');\n"
            "USE db;\n"
            f"{source.read_text(encoding='utf-8')}"
        )
        proc = subprocess.run(
            [str(duckdb), ":memory:"],
            input=sql,
            capture_output=True,
            text=True,
            cwd=working_dir,
        )
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout).strip().splitlines()
            detail = " | ".join(tail[-5:]) if tail else f"exit {proc.returncode}"
            raise RuntimeError(f"generating HTTPFS attach fixture failed: {detail}")
        os.replace(generated, destination)


def _prepare_seed_dir(config):
    working_dir = Path(get_context(config).working_dir)
    seed_dir = Path(scratch(config, "httpfs-minio", _PRESIGNED_PREFIX))
    seed_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(working_dir / "duckdb/data/csv/phonenumbers.csv", seed_dir / _SMALL_CSV)
    shutil.copy2(working_dir / "duckdb/data/parquet-testing/glob/t1.parquet", seed_dir / _SMALL_PARQUET)
    _generate_attach_database(config, seed_dir / _ATTACH_DB)
    return seed_dir


def httpfs_minio_populate(block, config):
    remote = minio_rclone(block)
    for bucket in (block["bucket"], SECONDARY_BUCKET, PUBLIC_BUCKET):
        mkdir(remote, bucket)
    minio_user_add(block, SECONDARY_USER, SECONDARY_PASSWORD)
    minio_policy_attach(block, "readwrite", user=SECONDARY_USER)
    minio_version_enable(block, block["bucket"])
    minio_anonymous_set(block, "public", PUBLIC_BUCKET)

    seed_dir = _prepare_seed_dir(config)
    data_dir = prepare_remote_data(config)
    temp_dir_root = Path(scratch(config, "httpfs-minio", "temp"))
    temp_dir_root.mkdir(parents=True, exist_ok=True)
    sync(str(seed_dir), remote, f"{block['bucket']}/{_PRESIGNED_PREFIX}")
    sync(str(data_dir), remote, f"{block['bucket']}/{block['data_prefix']}")

    def object_path(name):
        return f"{_PRESIGNED_PREFIX}/{name}"

    block["httpfs_env"] = {
        "S3_DATA_DIR": str(data_dir),
        "S3_TEMP_DIR_ROOT": str(temp_dir_root),
        "S3_ATTACH_DB": f"s3://{block['bucket']}/{object_path(_ATTACH_DB)}",
        "S3_ATTACH_DB_PRESIGNED_URL": minio_presigned_url(block, object_path(_ATTACH_DB)),
        "S3_SMALL_CSV_PRESIGNED_URL": minio_presigned_url(block, object_path(_SMALL_CSV)),
        "S3_SMALL_PARQUET_PRESIGNED_URL": minio_presigned_url(block, object_path(_SMALL_PARQUET)),
    }


HTTPFS_MINIO_BASE_SERVICE = minio_service(
    access_key=PRIMARY_USER,
    secret_key=PRIMARY_PASSWORD,
    region=REGION,
    bucket=PRIMARY_BUCKET,
    domain=MINIO_DOMAIN,
)

HTTPFS_MINIO_SERVICE = use_service(
    HTTPFS_MINIO_BASE_SERVICE,
    to_env=httpfs_minio_env,
    populate=httpfs_minio_populate,
)
