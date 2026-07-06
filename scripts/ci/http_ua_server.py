#!/usr/bin/env python3
import os
import sys
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

LOG_PATH = os.environ.get("HTTP_UA_LOG", "/logs/http-access.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

_lock = threading.Lock()
_log = open(LOG_PATH, "a", buffering=1)


class UALoggingHandler(SimpleHTTPRequestHandler):
    def log_request(self, code="-", size="-"):
        if isinstance(code, HTTPStatus):
            code = code.value
        ua = self.headers.get("User-Agent") or "-"
        with _lock:
            _log.write(f"{self.command} {self.path} {code} UA:{ua}\n")

    def log_message(self, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8008
    with ThreadingHTTPServer(("0.0.0.0", port), UALoggingHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
