#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/../.."

LOGS=test/httpfs_logs
DUCK_RE='^duckdb/'
# mc (MinIO setup/reset) is infra, not code under test -- ignore its requests.
INFRA_RE='mc/|minio-go'
chmod -R a+r "$LOGS" 2>/dev/null || true

status=0

# Classify "method<TAB>ua" lines; non-zero exit if any request lacked a duckdb UA.
classify() {
  awk -F'\t' -v src="$1" -v duck="$DUCK_RE" -v infra="$INFRA_RE" '
    { m=$1; ua=$2; tot[m]++
      if (m=="CONNECT") { connect++; next }
      if (ua ~ infra) { infra_c++; next }
      if (ua=="-" || ua=="") { miss[m]++; problems++; next }
      if (ua ~ duck) { ok[m]++; next }
      foreign[m]++; problems++; fua[ua]++ }
    END {
      total=0; for (m in tot) total+=tot[m]
      printf "[%s] %d requests", src, total
      if (connect) printf " (%d CONNECT ignored)", connect
      if (infra_c) printf " (%d infra ignored)", infra_c
      printf " -- problems: %d\n", problems+0
      n=split("GET PUT POST HEAD DELETE", order, " ")
      for (i=1;i<=n;i++) { m=order[i]; if (m in tot)
        printf "    %-7s ok=%-4d missing=%-4d foreign=%-4d\n", m, ok[m]+0, miss[m]+0, foreign[m]+0 }
      for (u in fua) printf "    !! foreign UA x%d: %s\n", fua[u], u
      exit (problems>0 ? 1 : 0) }'
}

if [[ -s "$LOGS/minio-trace.jsonl" ]]; then
  jq -r 'select(.request) | [.request.method, (.request.headers["User-Agent"] // "-")] | @tsv' "$LOGS/minio-trace.jsonl" \
    | classify minio || status=1
else
  echo "[minio] no trace captured"
fi

if [[ -s "$LOGS/http-access.log" ]]; then
  awk '{ ua=$0; sub(/^.*UA:/,"",ua); print $1"\t"ua }' "$LOGS/http-access.log" \
    | classify http || status=1
else
  echo "[http] no requests captured"
fi

if [[ -s "$LOGS/squid-access.log" ]]; then
  awk '{ i=index($0,"\"UA:"); ua=(i ? substr($0,i+4) : "-"); sub(/"$/,"",ua); print $4"\t"ua }' "$LOGS/squid-access.log" \
    | classify squid || status=1
else
  echo "[squid] no proxied requests"
fi

if [[ $status -ne 0 ]]; then
  echo "UA ASSERTION FAILED: requests without a duckdb/ User-Agent were found." >&2
else
  echo "UA assertion passed: every observed request carried a duckdb/ User-Agent."
fi
exit $status
