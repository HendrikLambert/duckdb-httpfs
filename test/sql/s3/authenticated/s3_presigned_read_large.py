from ducktest import requires, run_paired
from httpfs_ducktest.s3_data import S3Data


@requires(source=S3Data("lineitem_large"), access="ro", name="lineitem_large")
def test_s3_presigned_read_large(request, resources):
    run_paired(request, env=resources.env)
