import os
import shutil
from pathlib import Path

from ducktest import run_paired


def test_secret_compatibility_httpfs(request, tmp_path):
    source_dir = Path(request.config.rootpath) / "data" / "secrets" / "httpfs"
    fixture_dir = tmp_path / "httpfs-secrets"
    fixture_dir.mkdir()

    fixtures = list(source_dir.glob("*.duckdb_secret"))
    assert fixtures
    for source in fixtures:
        destination = fixture_dir / source.name
        shutil.copy2(source, destination)
        os.chmod(destination, 0o600)

    run_paired(
        request,
        env={
            "SECRET_FIXTURE_DIR": str(fixture_dir),
            "TEST_PERSISTENT_SECRETS_AVAILABLE": "1",
        },
    )
