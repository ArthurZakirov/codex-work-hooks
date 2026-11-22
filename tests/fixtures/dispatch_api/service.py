"""In-memory dispatch manifest service. Run with python service.py."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

manifests: dict[str, dict] = {}


class Handler(BaseHTTPRequestHandler):
    def reply(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        if self.path != "/manifests":
            return self.reply(404, {})
        try:
            record = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            identifier = record["id"]
            if not isinstance(identifier, str) or not identifier:
                raise ValueError
        except (TypeError, ValueError, KeyError):
            return self.reply(400, {"error": "expected manifest with string id"})
        manifests[identifier] = record
        self.reply(201, record)

    def do_GET(self) -> None:
        prefix = "/manifests/"
        if self.path.startswith(prefix) and self.path[len(prefix):] in manifests:
            return self.reply(200, manifests[self.path[len(prefix):]])
        self.reply(404, {})


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
