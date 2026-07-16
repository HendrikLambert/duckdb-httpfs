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
    # An empty Accept-Encoding means "identity only", so it counts as a failure, not a pass.
    by_source = group_by_source(requests)
    failures: list[Request] = []

    for source in SOURCES:
        source_requests = by_source.get(source, [])
        totals = Counter(request.method for request in source_requests)
        kept, ignored_connect, ignored_infra = relevant_requests(source, source_requests)

        ok = Counter()
        missing = Counter()
        empty = Counter()

        for request in kept:
            method = request.method
            if "accept-encoding" not in request.headers:
                missing[method] += 1
                failures.append(request)
                continue
            if not request.headers["accept-encoding"].strip():
                empty[method] += 1
                failures.append(request)
                continue
            ok[method] += 1

        total = sum(totals.values())
        suffix = ignored_suffix(ignored_connect, ignored_infra)
        problems = sum(missing.values()) + sum(empty.values())
        print(f"[{source}] {total} requests{suffix} -- problems: {problems}")

        for method in METHOD_ORDER:
            if method in totals:
                print(
                    f"    {method:<7} ok={ok[method]:<4} "
                    f"missing={missing[method]:<4} empty={empty[method]:<4}"
                )

    if failures:
        examples = "\n".join(format_request(request, "accept-encoding") for request in failures[:10])
        more = "" if len(failures) <= 10 else f"\n  ... {len(failures) - 10} more"
        raise LogAssertionError(
            "ACCEPT-ENCODING ASSERTION FAILED: requests without a non-empty Accept-Encoding were found.\n"
            f"{examples}{more}"
        )
