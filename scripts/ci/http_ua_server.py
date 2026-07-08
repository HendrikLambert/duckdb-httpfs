#!/usr/bin/env python3
"""Test-only HTTP server that logs every request's full header set as JSONL."""
import json
import os
import sys
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

LOG_PATH = os.environ.get("HTTP_UA_LOG", "/logs/http-access.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

_lock = threading.Lock()
_log = open(LOG_PATH, "a", buffering=1)


class HeaderLoggingHandler(SimpleHTTPRequestHandler):
    def send_response(self, code, message=None):
        if isinstance(code, HTTPStatus):
            code = code.value
        self._response_status = code if isinstance(code, int) else None
        self._response_headers = {}
        super().send_response(code, message)

    def send_header(self, keyword, value):
        if not hasattr(self, "_response_headers"):
            self._response_headers = {}
        self._response_headers[keyword.lower()] = str(value)
        super().send_header(keyword, value)

    def end_headers(self):
        super().end_headers()
        self._write_log()

    def log_request(self, code="-", size="-"):
        pass

    def _write_log(self):
        entry = {
            "request": {
                "method": self.command,
                "path": self.path,
                "headers": {key.lower(): value for key, value in self.headers.items()},
            },
            "response": {
                "status": getattr(self, "_response_status", None),
                "headers": getattr(self, "_response_headers", {}),
            },
        }
        with _lock:
            _log.write(json.dumps(entry) + "\n")

    def log_message(self, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8008
    with ThreadingHTTPServer(("0.0.0.0", port), HeaderLoggingHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
