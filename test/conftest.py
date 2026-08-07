from ducktest import env_ref, register_suite
from ducktest.resources.ca import CA_SERVICE
from httpfs_ducktest.httpfs_http import HTTPFS_HTTP_SERVICE
from httpfs_ducktest.httpfs_minio import HTTPFS_MINIO_SERVICE
from httpfs_ducktest.httpfs_mitm import HTTPFS_MITM_SERVICE
from httpfs_ducktest.s3_data import S3DataProvisioner

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
        "local_data_dir": env_ref("S3_DATA_DIR"),
        "temp_dir_root": env_ref("S3_TEMP_URI_ROOT"),
        "local_temp_dir_root": env_ref("S3_TEMP_DIR_ROOT"),
        "S3_ACCESS_KEY_ID": env_ref("S3_ACCESS_KEY_ID"),
        "S3_SECRET_ACCESS_KEY": env_ref("S3_SECRET_ACCESS_KEY"),
        "S3_REGION": env_ref("S3_REGION"),
        "S3_ENDPOINT": env_ref("S3_ENDPOINT"),
        "S3_USE_SSL": env_ref("S3_USE_SSL"),
    },
}

S3_PUBLIC_CELL = {
    "id": "s3-public",
    "properties": {
        **S3_CELL["properties"],
        "temp_dir_root": env_ref("S3_PUBLIC_TEMP_URI_ROOT"),
    },
}

def pytest_configure(config):
    config.addinivalue_line("markers", "todo: HTTPFS tests not yet migrated to a ducktest suite.")
    config.addinivalue_line("markers", "local: service-free HTTPFS tests.")
    config.addinivalue_line("markers", "http: HTTP-specific tests backed by the managed HTTP origin.")
    config.addinivalue_line("markers", "s3: S3-specific tests backed by managed MinIO.")
    config.addinivalue_line("markers", "s3_public: public-bucket S3 tests backed by managed MinIO.")
    config.addinivalue_line("markers", "remote: backend-neutral tests run against HTTP and S3.")
    config.addinivalue_line("markers", "proxy: HTTP proxy behavior backed by managed mitmproxy and MinIO.")
    config.addinivalue_line("markers", "external: tests against real public HTTP providers.")

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
        path="test/sql/s3/authenticated",
        services=[HTTPFS_MINIO_SERVICE],
        provisioner=S3DataProvisioner(config),
        matrix=[S3_CELL],
    )
    register_suite(
        config,
        "s3_public",
        path="test/sql/s3/public",
        services=[HTTPFS_MINIO_SERVICE],
        matrix=[S3_PUBLIC_CELL],
    )
    register_suite(
        config,
        "remote",
        path="test/sql/remote",
        services=[HTTPFS_HTTP_SERVICE, HTTPFS_MINIO_SERVICE],
        matrix=[HTTP_CELL, S3_CELL],
    )
    register_suite(
        config,
        "proxy",
        path="test/sql/proxy",
        services=[CA_SERVICE, HTTPFS_MINIO_SERVICE, HTTPFS_MITM_SERVICE],
        matrix=[S3_CELL],
    )
    register_suite(config, "external", path="test/sql/external", default=False)
