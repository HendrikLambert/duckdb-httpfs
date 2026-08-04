from ducktest import run_paired


def test_parquet_force_download_threshold(request):
    run_paired(
        request,
        env={
            "S3_TEST_SERVER_AVAILABLE": "1",
            "AWS_ACCESS_KEY_ID": "ducktest-invalid-access-key",
            "AWS_SECRET_ACCESS_KEY": "ducktest-invalid-secret-key",
        },
    )
