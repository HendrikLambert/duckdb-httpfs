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
    def log_request(self, code="-", size="-"):
        if isinstance(code, HTTPStatus):
            code = code.value
        headers = {key.lower(): value for key, value in self.headers.items()}
        entry = {
            "method": self.command,
            "path": self.path,
            "status": code if isinstance(code, int) else None,
            "headers": headers,
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
