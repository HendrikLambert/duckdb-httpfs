from ducktest import run_paired
from ducktest.resources.mitm_addon import require_auth
from ducktest.resources.mitm_profile import proxy_init_sql
from httpfs_ducktest.httpfs_mitm import PROXY_PASSWORD, PROXY_USERNAME


def test_http_proxy_auth(request, matrix_cell):
    run_paired(
        request,
        init_sql=proxy_init_sql(require_auth(username=PROXY_USERNAME, password=PROXY_PASSWORD)),
    )
