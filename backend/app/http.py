import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import store


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = (ROOT / "frontend").resolve()
REPORT_PATH = (ROOT / "evaluation" / "report.md").resolve()


class Handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/summary":
                self.json(store.summary())
                return

            if parsed.path == "/api/audit":
                qs = parse_qs(parsed.query)
                try:
                    limit = min(500, max(1, int(qs.get("limit", ["100"])[0])))
                except (ValueError, IndexError):
                    limit = 100
                self.json(store.list_recent_audits(limit))
                return

            if parsed.path == "/api/evaluation":
                if REPORT_PATH.exists():
                    self.json({"report": REPORT_PATH.read_text(encoding="utf-8")})
                else:
                    self.json({"report": "Report not generated yet. Run scripts/evaluate.py."})
                return

            if parsed.path == "/api/payments":
                qs = parse_qs(parsed.query)
                try:
                    limit = min(200, max(1, int(qs.get("limit", ["50"])[0])))
                except (ValueError, IndexError):
                    limit = 50
                filter_type = qs.get("filter", [None])[0]
                self.json(store.list_cases(limit=limit, filter_type=filter_type))
                return

            if parsed.path.startswith("/api/payments/"):
                payment_id = parsed.path.rsplit("/", 1)[-1].strip()
                store.ensure_loaded()
                if payment_id not in store.payments:
                    self.json({"error": "Payment not found"}, status=404)
                    return
                self.json(store.enrich(store.payments[payment_id]))
                return

            self.static(parsed.path)
        except Exception as exc:
            self.json({"error": f"Internal Server Error: {str(exc)}"}, status=500)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/demo/reset":
                store.load_payments()
                self.json(store.summary())
                return

            if parsed.path == "/api/demo/run-batch":
                qs = parse_qs(parsed.query)
                try:
                    limit = int(qs.get("limit", ["600"])[0])
                except (ValueError, IndexError):
                    limit = 600
                self.json(store.run_batch(limit=limit))
                return

            if parsed.path.startswith("/api/payments/") and parsed.path.endswith("/execute"):
                parts = parsed.path.strip("/").split("/")
                if len(parts) >= 2:
                    payment_id = parts[1]
                    store.ensure_loaded()
                    if payment_id not in store.payments:
                        self.json({"error": "Payment not found"}, status=404)
                        return
                    self.json(store.execute(payment_id))
                    return

            self.json({"error": "Endpoint not found"}, status=404)
        except Exception as exc:
            self.json({"error": f"Internal Server Error: {str(exc)}"}, status=500)

    def static(self, path: str) -> None:
        clean_path = "index.html" if path in {"", "/"} else path.lstrip("/")
        target = (FRONTEND / clean_path).resolve()

        # Security check: Prevent path traversal outside FRONTEND root
        if not target.is_relative_to(FRONTEND) or not target.exists() or not target.is_file():
            self.json({"error": "File not found"}, status=404)
            return

        content_type, _ = mimetypes.guess_type(str(target))
        if not content_type:
            if target.suffix == ".css":
                content_type = "text/css"
            elif target.suffix == ".js":
                content_type = "application/javascript"
            elif target.suffix == ".json":
                content_type = "application/json"
            elif target.suffix == ".svg":
                content_type = "image/svg+xml"
            else:
                content_type = "text/plain"

        body = target.read_bytes()
        self.send_response(200)
        self._set_cors_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        # Suppress routine console logs for cleaner test runner output
        return


def run(host: str | None = None, port: int | None = None) -> None:
    import os

    actual_host = host or os.environ.get("HOST", "0.0.0.0")
    actual_port = int(port or os.environ.get("PORT", 8000))

    store.ensure_loaded()
    server = ThreadingHTTPServer((actual_host, actual_port), Handler)
    print(f"ReviveAI running at http://{actual_host}:{actual_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping ReviveAI server...")
        server.server_close()
