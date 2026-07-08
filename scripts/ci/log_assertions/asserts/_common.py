"""Shared helpers for the asserts. The leading _ keeps run.py from loading it as an assertion."""
from collections import defaultdict

from model import Request

INFRA_USER_AGENT_PARTS = ("mc/", "minio-go")
METHOD_ORDER = ("GET", "PUT", "POST", "HEAD", "DELETE")
SOURCES = ("minio", "http", "squid")


def is_infra_user_agent(user_agent: str) -> bool:
    return any(part in user_agent for part in INFRA_USER_AGENT_PARTS)


def group_by_source(requests: list[Request]) -> dict[str, list[Request]]:
    by_source: dict[str, list[Request]] = defaultdict(list)
    for request in requests:
        by_source[request.source].append(request)
    return by_source


def relevant_requests(source: str, source_requests: list[Request]) -> tuple[list[Request], int, int]:
    """Return (kept, ignored_connect, ignored_infra), dropping squid CONNECT tunnels and infra traffic."""
    kept: list[Request] = []
    ignored_connect = 0
    ignored_infra = 0
    for request in source_requests:
        if source == "squid" and request.method == "CONNECT":
            ignored_connect += 1
            continue
        if is_infra_user_agent(request.headers.get("user-agent", "")):
            ignored_infra += 1
            continue
        kept.append(request)
    return kept, ignored_connect, ignored_infra


def ignored_suffix(ignored_connect: int, ignored_infra: int) -> str:
    details = []
    if ignored_connect:
        details.append(f"{ignored_connect} CONNECT ignored")
    if ignored_infra:
        details.append(f"{ignored_infra} infra ignored")
    return f" ({', '.join(details)})" if details else ""


def format_request(request: Request, header: str) -> str:
    value = request.headers.get(header)
    shown = "<absent>" if value is None else (value or "<empty>")
    return "\n".join(
        [
            f"  {request.source} line {request.line_no}:",
            f"    {request.method or '<unknown>'} {request.path or '<unknown>'}",
            f"    status={request.response.status if request.response.status is not None else '-'}",
            f"    {header}={shown}",
            f"    raw={request.raw[:500]}",
        ]
    )
