from collections import Counter

from model import LogAssertionError, Request

from ._common import (
    METHOD_ORDER,
    SOURCES,
    format_request,
    group_by_source,
    ignored_suffix,
    relevant_requests,
)


def assert_requests(requests: list[Request]) -> None:
    by_source = group_by_source(requests)
    failures: list[Request] = []

    for source in SOURCES:
        source_requests = by_source.get(source, [])
        totals = Counter(request.method for request in source_requests)
        kept, ignored_connect, ignored_infra = relevant_requests(source, source_requests)

        ok = Counter()
        missing = Counter()
        foreign = Counter()
        foreign_user_agents = Counter()

        for request in kept:
            method = request.method
            user_agent = request.headers.get("user-agent", "")

            if not user_agent or user_agent == "-":
                missing[method] += 1
                failures.append(request)
                continue
            if user_agent.startswith("duckdb/"):
                ok[method] += 1
                continue

            foreign[method] += 1
            foreign_user_agents[user_agent] += 1
            failures.append(request)

        total = sum(totals.values())
        suffix = ignored_suffix(ignored_connect, ignored_infra)
        problems = sum(missing.values()) + sum(foreign.values())
        print(f"[{source}] {total} requests{suffix} -- problems: {problems}")

        for method in METHOD_ORDER:
            if method in totals:
                print(
                    f"    {method:<7} ok={ok[method]:<4} "
                    f"missing={missing[method]:<4} foreign={foreign[method]:<4}"
                )
        for user_agent, count in foreign_user_agents.items():
            print(f"    !! foreign UA x{count}: {user_agent}")

    if failures:
        examples = "\n".join(format_request(request, "user-agent") for request in failures[:10])
        more = "" if len(failures) <= 10 else f"\n  ... {len(failures) - 10} more"
        raise LogAssertionError(
            "UA ASSERTION FAILED: requests without a duckdb/ User-Agent were found.\n"
            f"{examples}{more}"
        )
