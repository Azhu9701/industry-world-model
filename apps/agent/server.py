import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def discover_names(root: str, marker: str) -> list[str]:
    path = Path(root)
    if not path.is_dir():
        return []
    return sorted(item.name for item in path.iterdir() if (item / marker).is_file())


def api_request(path: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    base = os.getenv("IWM_API_URL", "http://api:8080").rstrip("/")
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    key = os.getenv("IWM_WRITE_KEY")
    if key:
        headers["x-iwm-key"] = key
    request = urllib.request.Request(f"{base}{path}", data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        try:
            data = json.loads(error.read().decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = {"error": f"upstream returned HTTP {error.code}"}
        return error.code, data
    except OSError as error:
        return 503, {"error": f"API unavailable: {error}"}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            status, api = api_request("/health")
            self._json(200 if status == 200 else 503, {
                "status": "ok" if status == 200 else "degraded",
                "api": api,
            })
        elif self.path == "/api/v1/capabilities":
            packs = discover_names(os.getenv("PACKS_DIR", "packs"), "domain.yaml")
            skills = discover_names(os.getenv("SKILLS_DIR", "skills"), "SKILL.md")
            status, meta = api_request("/api/v1/meta")
            self._json(200, {
                "version": "0.2.0",
                "defaultPack": os.getenv("DEFAULT_PACK", "example"),
                "packs": packs,
                "skills": skills,
                "writesEnabled": bool(meta.get("writesEnabled")) if status == 200 else False,
                "proposalEndpoint": "/api/v1/proposals",
                "workflow": ["discover", "extract", "verify", "propose", "review"],
            })
        elif self.path == "/api/v1/packs":
            status, payload = api_request("/api/v1/packs")
            self._json(status, payload)
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/api/v1/proposals":
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1_000_000:
                self._json(400, {"error": "request body must be between 1 byte and 1 MB"})
                return
            payload = json.loads(self.rfile.read(length).decode())
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object")
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as error:
            self._json(400, {"error": str(error)})
            return

        payload.setdefault("pack", os.getenv("DEFAULT_PACK", "example"))
        status, response = api_request(
            "/api/v1/ingest/proposals",
            method="POST",
            payload=payload,
        )
        self._json(status, response)

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"agent {self.address_string()} {format % args}")


if __name__ == "__main__":
    port = int(os.getenv("AGENT_PORT", "8090"))
    print(f"industry-world-model agent v0.2 listening on 0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
