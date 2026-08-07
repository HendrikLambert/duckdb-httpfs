import pytest

from ducktest import run_paired


@pytest.mark.parametrize("client", ["curl", "httplib"])
def test_check_glob_error_message(request, client):
    run_paired(
        request,
        init_sql=f"LOAD httpfs; SET httpfs_client_implementation='{client}';",
    )
