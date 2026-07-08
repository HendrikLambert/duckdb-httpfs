import json
import re
import urllib.parse
from collections.abc import Iterable
from pathlib import Path

from model import Request, Response, normalize_headers


SQUID_RE = re.compile(
    r"^(?P<timestamp>\S+)\s+(?P<client>\S+)\s+(?P<result>\S+)\s+"
    r"(?P<method>\S+)\s+(?P<path>\S+)\s+(?P<request_headers>\S*)\s+(?P<response_headers>\S*)$"
)


def _decode_squid_headers(blob: str) -> dict[str, str]:
    """Decode squid's URL-encoded %#>h header block into a header map."""
    if not blob or blob == "-":
        return {}
    headers: dict[str, str] = {}
    for header_line in urllib.parse.unquote(blob).split("\r\n"):
        name, sep, value = header_line.partition(":")
        if not sep:
            continue
        headers[name.strip().lower()] = value.strip()
    return headers


def parse_minio(path: Path) -> Iterable[Request]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            raw = line.rstrip("\n")
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                yield Request(source="minio", line_no=line_no, method="", path=None, raw=raw)
                continue

            request = entry.get("request") or {}
            response = entry.get("response") or {}
            yield Request(
                source="minio",
                line_no=line_no,
                method=str(request.get("method") or ""),
                path=request.get("path") or entry.get("path"),
                headers=normalize_headers(request.get("headers")),
                response=Response(
                    status=response.get("statusCode"),
                    headers=normalize_headers(response.get("headers")),
                ),
                raw=raw,
                meta={
                    "api": str(entry.get("api") or ""),
                    "host": str(entry.get("host") or ""),
                    "raw_query": str(request.get("rawQuery") or ""),
                },
            )


def parse_http(path: Path) -> Iterable[Request]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            raw = line.rstrip("\n")
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                yield Request(source="http", line_no=line_no, method="", path=None, raw=raw)
                continue
            request = entry.get("request") or {}
            response = entry.get("response") or {}
            yield Request(
                source="http",
                line_no=line_no,
                method=str(request.get("method") or ""),
                path=request.get("path"),
                headers=normalize_headers(request.get("headers")),
                response=Response(
                    status=response.get("status"),
                    headers=normalize_headers(response.get("headers")),
                ),
                raw=raw,
            )


def parse_squid(path: Path) -> Iterable[Request]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            raw = line.rstrip("\n")
            if not raw:
                continue
            match = SQUID_RE.match(raw)
            if not match:
                yield Request(source="squid", line_no=line_no, method="", path=None, raw=raw)
                continue

            status = None
            if "/" in match.group("result"):
                _, status_text = match.group("result").rsplit("/", 1)
                if status_text.isdigit():
                    status = int(status_text)

            yield Request(
                source="squid",
                line_no=line_no,
                method=match.group("method"),
                path=match.group("path"),
                headers=_decode_squid_headers(match.group("request_headers")),
                response=Response(
                    status=status,
                    headers=_decode_squid_headers(match.group("response_headers")),
                ),
                raw=raw,
                meta={"client": match.group("client"), "result": match.group("result")},
            )


PARSERS = {
    "minio": ("minio-trace.jsonl", parse_minio, "no trace captured"),
    "http": ("http-access.log", parse_http, "no requests captured"),
    "squid": ("squid-access.log", parse_squid, "no proxied requests"),
}


def parse_logs(log_dir: Path) -> tuple[list[Request], dict[str, int]]:
    requests: list[Request] = []
    counts: dict[str, int] = {}
    for source, (filename, parser, empty_message) in PARSERS.items():
        path = log_dir / filename
        if not path.exists() or path.stat().st_size == 0:
            print(f"[{source}] {empty_message}")
            counts[source] = 0
            continue
        parsed = list(parser(path))
        requests.extend(parsed)
        counts[source] = len(parsed)
    return requests, counts
