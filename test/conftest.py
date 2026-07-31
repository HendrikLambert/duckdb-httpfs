from pathlib import Path

import pytest

from ducktest import env_ref, register_suite
from httpfs_ducktest.httpfs_http import HTTPFS_HTTP_SERVICE
from httpfs_ducktest.httpfs_minio import HTTPFS_MINIO_SERVICE


S3_REQUIRE_ENV = "require-env S3_TEST_SERVER_AVAILABLE"
TODO_DIR = Path(__file__).parent / "sql" / "todo"

HTTP_CELL = {
    "id": "http",
    "properties": {
        "data_dir": env_ref("HTTP_DATA_URL"),
        "local_data_dir": env_ref("HTTP_DATA_DIR"),
        "temp_dir_root": env_ref("HTTP_TEMP_URL_ROOT"),
        "local_temp_dir_root": env_ref("HTTP_TEMP_DIR_ROOT"),
    },
}

S3_CELL = {
    "id": "s3",
    "properties": {
        "data_dir": env_ref("S3_DATA_URI"),
        "temp_dir_root": env_ref("S3_TEMP_URI_ROOT"),
        "S3_ACCESS_KEY_ID": env_ref("S3_ACCESS_KEY_ID"),
        "S3_SECRET_ACCESS_KEY": env_ref("S3_SECRET_ACCESS_KEY"),
        "S3_REGION": env_ref("S3_REGION"),
        "S3_ENDPOINT": env_ref("S3_ENDPOINT"),
        "S3_USE_SSL": env_ref("S3_USE_SSL"),
    },
}


def pytest_configure(config):
    config.addinivalue_line("markers", "todo: HTTPFS tests not yet migrated to a ducktest suite.")
    config.addinivalue_line("markers", "local: service-free HTTPFS tests.")
    config.addinivalue_line("markers", "http: HTTP-specific tests backed by the managed HTTP origin.")
    config.addinivalue_line("markers", "s3: S3-specific tests backed by managed MinIO.")
    config.addinivalue_line("markers", "remote: backend-neutral tests run against HTTP and S3.")
    config.addinivalue_line("markers", "minio_s3: legacy TODO tests backed by managed MinIO.")

    register_suite(config, "todo", path="test/sql/todo", default=False)
    register_suite(config, "local", path="test/sql/local")
    register_suite(
        config,
        "http",
        path="test/sql/http",
        services=[HTTPFS_HTTP_SERVICE],
        matrix=[HTTP_CELL],
    )
    register_suite(
        config,
        "s3",
        path="test/sql/s3",
        default=False,
        services=[HTTPFS_MINIO_SERVICE],
        matrix=[S3_CELL],
    )
    register_suite(
        config,
        "remote",
        path="test/sql/remote",
        default=False,
        services=[HTTPFS_HTTP_SERVICE, HTTPFS_MINIO_SERVICE],
        matrix=[HTTP_CELL, S3_CELL],
    )
    register_suite(
        config,
        "minio_s3",
        marker="minio_s3",
        default=False,
        services=[HTTPFS_MINIO_SERVICE],
    )


def _needs_minio(item):
    path = getattr(item, "path", None)
    if path is None:
        return False
    try:
        path.relative_to(TODO_DIR)
    except ValueError:
        return False
    try:
        return S3_REQUIRE_ENV in path.read_text(encoding="utf-8")
    except OSError:
        return False


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection_modifyitems(config, items):
    for item in items:
        if _needs_minio(item):
            item.add_marker("minio_s3")
    yield
