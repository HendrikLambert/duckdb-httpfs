## Running the httpfs integration tests

The integration tests run the httpfs suite against a Docker stack that mirrors CI
exactly: MinIO (S3), a Squid proxy, and a Python HTTP server. The same
`scripts/ci` entrypoints are used locally and in
[`.github/workflows/IntegrationTests.yml`](../.github/workflows/IntegrationTests.yml),
so a green run locally means a green run in CI.

Requires Docker. On macOS: `brew install docker --cask`, then open
`/Applications/Docker` once to finish setup.

### One-time host setup

The host runs the `unittest` binary directly against the containers, so it needs
`/etc/hosts` aliases pointing the MinIO vhosts at localhost (and the checked-in
test secrets restricted to 0700, which duckdb requires). Run once:

```bash
sudo ./scripts/ci/setup-hosts.sh
```

### Run everything

```bash
make                              # build the extension (produces build/release/test/unittest)
./scripts/ci/run-ci-pipeline.sh   # generate data (if missing) -> up -> tests -> assert logs -> teardown
```

The pipeline:

1. `scripts/ci/generate-data.sh` — generates the test data into `test/test_data/`
   if missing, using the `duckdb/duckdb:1.5.2` container (matching the pinned
   submodule, so no local duckdb build is needed just for data).
2. `scripts/ci/up.sh` — brings up `scripts/ci/docker-compose.yml`, waits for MinIO
   setup, and writes the scraped presigned URLs to `test/httpfs_logs/presigned.env`.
3. `scripts/ci/run-tests.sh` — runs the unittest suite (curl / httplib / caching
   variants) against the stack.
4. `scripts/ci/assert-logs.sh` — checks every request captured by MinIO, the HTTP
   server, and Squid carried a `duckdb/` User-Agent, and **fails** otherwise.

Captured logs land in `test/httpfs_logs/` (`minio-trace.jsonl`, `http-access.log`,
`squid-access.log`); both `test/test_data/` and `test/httpfs_logs/` are gitignored.

### Local iteration

```bash
# keep the stack up and narrow the tests while debugging
KEEP_UP=1 TEST_FILTER='test/sql/copy/s3/*' ./scripts/ci/run-ci-pipeline.sh

# or drive a single step against an already-running stack
source scripts/ci/set-ci-env.sh
source test/httpfs_logs/presigned.env
build/release/test/unittest test/sql/copy/s3/s3_hive_partition.test
```

Regenerate the test data from scratch with `./scripts/ci/generate-data.sh --force`.

> MinIO uses port 9000. Clickhouse also uses port 9000 — if tests fail and you have
> a running Clickhouse service, kill it first (`killall -9 clickhouse`).
