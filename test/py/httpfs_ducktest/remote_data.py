import shutil
from pathlib import Path

from ducktest import get_context
from ducktest.workspace import scratch


def prepare_remote_data(config):
    working_dir = Path(get_context(config).working_dir)
    data_dir = Path(scratch(config, "httpfs-data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        working_dir / "duckdb/data/parquet-testing/userdata1.parquet",
        data_dir / "userdata1.parquet",
    )
    return data_dir
