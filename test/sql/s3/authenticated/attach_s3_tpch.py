from ducktest import requires, run_paired
from httpfs_ducktest.s3_data import S3Data


@requires(source=S3Data("lineitem_sf1"), access="ro", name="lineitem_sf1")
def test_attach_s3_tpch(request, resources):
    run_paired(request, env=resources.env)
