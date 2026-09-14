import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def discover_names(root: str, marker: str) -> list[str]:
    path = Path(root)
    if not path.is_dir():
        return []
    return sorted(item.name for item in path.iterdir() if (item / marker).is_file())


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {"status": "ok"})
        elif self.path == "/api/v1/capabilities":
            packs = discover_names(os.getenv("PACKS_DIR", "packs"), "domain.yaml")
            skills = discover_names(os.getenv("SKILLS_DIR", "skills"), "SKILL.md")
            self._json(200, {
                "defaultPack": os.getenv("DEFAULT_PACK", "example"),
                "packs": packs,
                "skills": skills,
                "writesEnabled": False,
            })
        else:
            self._json(404, {"error": "not found"})

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
    print(f"industry-world-model agent listening on 0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
