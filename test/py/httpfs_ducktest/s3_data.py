from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from ducktest import Provisioner, State, find_duckdb, get_context, provision_service, sql_literal
from ducktest.resources.minio import minio_presigned_url, minio_rclone
from ducktest.tools.rclone import seed
from ducktest.workspace import scratch

from .httpfs_minio import HTTPFS_MINIO_SERVICE, PRIMARY_BUCKET

_REMOTE_PREFIX = "large-fixtures"


@dataclass(frozen=True)
class S3Data:
    name: str


@dataclass(frozen=True)
class _Fixture:
    filename: str
    env_name: str
    presigned: bool = False


@dataclass
class _S3DataState(State):
    block: dict | None = None
    fixtures: dict = field(default_factory=dict)


_FIXTURES = {
    "lineitem_sf1": _Fixture("lineitem_sf1.db", "S3_LINEITEM_SF1_DB"),
    "lineitem_large": _Fixture(
        "lineitem_large.parquet",
        "S3_LARGE_PARQUET_PRESIGNED_URL",
        presigned=True,
    ),
}


def _fixture(source):
    if not isinstance(source, S3Data) or source.name not in _FIXTURES:
        raise pytest.UsageError(f"unknown HTTPFS S3 data source: {source!r}")
    return _FIXTURES[source.name]


def _run_duckdb(config, database, sql):
    working_dir = Path(get_context(config).working_dir)
    duckdb = Path(find_duckdb(config, str(working_dir)))
    proc = subprocess.run(
        [str(duckdb), str(database), "-c", sql],
        capture_output=True,
        text=True,
        cwd=working_dir,
        check=False,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout).strip().splitlines()
        detail = " | ".join(tail[-5:]) if tail else f"exit {proc.returncode}"
        raise RuntimeError(f"generating HTTPFS S3 fixture failed: {detail}")


def _generate(config, source, destination):
    working_dir = Path(get_context(config).working_dir)
    duckdb = Path(find_duckdb(config, str(working_dir)))
    if destination.exists() and destination.stat().st_mtime_ns >= duckdb.stat().st_mtime_ns:
        return

    with tempfile.TemporaryDirectory(prefix=f"{source.name}-", dir=destination.parent) as tmp:
        generated = Path(tmp) / destination.name
        if source.name == "lineitem_sf1":
            _run_duckdb(config, generated, "CALL dbgen(sf=1);")
        else:
            sql = (
                "CALL dbgen(sf=1); "
                f"COPY lineitem TO {sql_literal(str(generated))} (FORMAT PARQUET);"
            )
            _run_duckdb(config, ":memory:", sql)
        os.replace(generated, destination)


class S3DataProvisioner(Provisioner):
    def __init__(self, config):
        super().__init__()
        self._config = config
        self._dry_run = False

    def backend(self):
        return "httpfs-s3-data"

    def before_provision(self, specs, token, dry_run):
        self._dry_run = dry_run
        for spec in specs:
            _fixture(spec.source)
            if spec.access != "ro":
                raise pytest.UsageError("HTTPFS S3 data fixtures only support access='ro'")

    def new_state(self, token, *, params=None):
        block = None if self._dry_run else provision_service(self._config, HTTPFS_MINIO_SERVICE)
        return _S3DataState(token=token, block=block)

    def ro_target(self, spec, state):
        fixture = _fixture(spec.source)
        prefix = f"{_REMOTE_PREFIX}/{spec.source.name}"
        object_path = f"{prefix}/{fixture.filename}"
        bucket = state.block["bucket"] if state.block else PRIMARY_BUCKET
        target = f"{bucket}/{prefix}"
        state.fixtures[target] = (spec.source, fixture, object_path)
        return target

    def instantiate(self, spec, target, dry_run, state):
        source, fixture, _ = state.fixtures[target]
        state.plan.append(f"[ro] seed {target} from {fixture.filename}")
        if dry_run:
            return

        source_dir = Path(scratch(self._config, "httpfs-minio", "large-fixtures", source.name))
        destination = source_dir / fixture.filename
        _generate(self._config, source, destination)
        seed(
            minio_rclone(state.block),
            str(source_dir),
            state.block["bucket"],
            f"{_REMOTE_PREFIX}/{source.name}",
            access="ro",
        )

    def env_for(self, state):
        env = {}
        bucket = state.block["bucket"] if state.block else PRIMARY_BUCKET
        for _, fixture, object_path in state.fixtures.values():
            if fixture.presigned:
                value = (
                    f"<presigned:{object_path}>"
                    if self._dry_run
                    else minio_presigned_url(state.block, object_path)
                )
            else:
                value = f"s3://{bucket}/{object_path}"
            env[fixture.env_name] = value
        return env

    def rw_target(self, spec, token, state, dry_run):
        raise pytest.UsageError("HTTPFS S3 data fixtures only support access='ro'")

    def make_init_sql(self, bindings, *, redact=False):
        return ""
