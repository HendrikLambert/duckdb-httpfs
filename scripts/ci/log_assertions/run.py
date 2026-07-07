import argparse
import importlib
import pkgutil
import sys
from pathlib import Path

from model import LogAssertionError
from parsers import parse_logs


def load_assertions():
    package_name = "asserts"
    package = importlib.import_module(package_name)
    modules = []
    for module_info in pkgutil.iter_modules(package.__path__):
        if module_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{package_name}.{module_info.name}")
        if hasattr(module, "assert_requests"):
            modules.append(module)
    return modules


def main() -> int:
    parser = argparse.ArgumentParser(description="Assert invariants over httpfs CI logs")
    parser.add_argument("--logs", default="test/httpfs_logs", type=Path)
    args = parser.parse_args()

    requests, _ = parse_logs(args.logs)

    failures = []
    for assertion in load_assertions():
        name = assertion.__name__.rsplit(".", 1)[-1]
        print()
        print(f"==== {name}.py ".ljust(60, "="))
        try:
            assertion.assert_requests(requests)
        except LogAssertionError as exc:
            failures.append(str(exc))

    if failures:
        sys.stdout.flush()  # keep the per-assert overview above the failure detail
        print("\n==== log assertion failures ====", file=sys.stderr)
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
