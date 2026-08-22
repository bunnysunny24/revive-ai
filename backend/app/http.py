import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import store


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/summary":
            self.json(store.summary())
            return

        if parsed.path == "/api/payments":
            limit = int(parse_qs(parsed.query).get("limit", ["25"])[0])
            self.json(store.list_cases(limit))
            return

        if parsed.path.startswith("/api/payments/"):
            payment_id = parsed.path.rsplit("/", 1)[-1]
            store.ensure_loaded()
            if payment_id not in store.payments:
                self.json({"error": "payment not found"}, status=404)
                return
            self.json(store.enrich(store.payments[payment_id]))
            return

        self.static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/demo/reset":
            store.load_payments()
            self.json(store.summary())
            return

        if parsed.path == "/api/demo/run-batch":
            self.json(store.run_batch())
            return

        if parsed.path.startswith("/api/payments/") and parsed.path.endswith("/execute"):
            payment_id = parsed.path.split("/")[-2]
            store.ensure_loaded()
            if payment_id not in store.payments:
                self.json({"error": "payment not found"}, status=404)
                return
            self.json(store.execute(payment_id))
            return

        self.json({"error": "not found"}, status=404)

    def static(self, path: str) -> None:
        target = FRONTEND / ("index.html" if path == "/" else path.lstrip("/"))
        if not target.exists() or not target.is_file():
            self.json({"error": "not found"}, status=404)
            return

        content_type = "text/html"
        if target.suffix == ".css":
            content_type = "text/css"
        elif target.suffix == ".js":
            content_type = "application/javascript"

        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def run() -> None:
    store.ensure_loaded()
    server = ThreadingHTTPServer(("localhost", 8000), Handler)
    print("ReviveAI running at http://localhost:8000")
    server.serve_forever()
