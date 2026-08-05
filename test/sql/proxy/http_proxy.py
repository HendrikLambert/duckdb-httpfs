from ducktest import run_paired


def test_http_proxy(request, matrix_cell):
    run_paired(request)
