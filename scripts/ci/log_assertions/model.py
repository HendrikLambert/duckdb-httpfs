from dataclasses import dataclass, field


@dataclass(frozen=True)
class Request:
    source: str
    line_no: int
    method: str
    path: str | None
    status: int | None
    headers: dict[str, str] = field(default_factory=dict)
    raw: str = ""
    meta: dict[str, str] = field(default_factory=dict)


class LogAssertionError(AssertionError):
    pass


def normalize_headers(headers: dict[str, object] | None) -> dict[str, str]:
    if not headers:
        return {}
    return {str(key).lower(): "" if value is None else str(value) for key, value in headers.items()}
