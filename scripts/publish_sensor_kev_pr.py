#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "scripts" / "sensor_kev_to_contribution.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("sensor_kev_adapter", ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Sensor/Kev adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTER = load_adapter()


class PublishError(Exception):
    pass


def request_json(
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
    *,
    allow_404: bool = False,
) -> Any:
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "aiman-sensor-kev-contribution/0.1",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        if allow_404 and exc.code == 404:
            return None
        body = exc.read().decode(errors="replace")
        raise PublishError(
            f"GitHub API {method} {url} failed: HTTP {exc.code}: {body}"
        ) from exc


def repo_url(api_base: str, repository: str, suffix: str) -> str:
    return f"{api_base.rstrip('/')}/repos/{repository}{suffix}"


def branch_name(envelope: dict[str, Any]) -> str:
    return f"auto-contrib/{ADAPTER.slug(envelope['idempotency_key'])[:120]}"


def pr_title(envelope: dict[str, Any]) -> str:
    return f"contrib(robotics): {envelope['sensor']['title']}"[:240]


def pr_body(envelope: dict[str, Any], path: str) -> str:
    sensor = envelope["sensor"]
    decision = envelope["kev"]["decision_packet"]
    sources = "\n".join(f"- {source['url']}" for source in sensor["sources"])
    return (
        "Automated World Model contribution generated from the production "
        "Sensor -> AIMAN-Kev path.\n\n"
        "### Gate\n"
        f"- Sensor verification: {sensor['verification_status']}\n"
        f"- Kev model: {envelope['kev']['model']}\n"
        f"- event_type: {decision['event_type']}\n"
        f"- timeline_worthy: {str(decision['timeline_worthy']).lower()}\n"
        f"- commercialization_stage: {decision['commercialization_stage']}\n"
        f"- source_quality: {decision['source_quality']}\n"
        f"- needs_second_source: {str(decision['needs_second_source']).lower()}\n"
        f"- Contribution path: {path}\n\n"
        "### Evidence sources\n"
        f"{sources}\n\n"
        "Review-only: this automation never verifies, merges, or writes canonical facts."
    )


def publish(
    envelope: dict[str, Any],
    *,
    token: str,
    repository: str,
    base: str,
    api_base: str,
) -> dict[str, Any]:
    ok, reasons, mapped = ADAPTER.eligibility(envelope)
    if not ok:
        return {
            "status": "skipped",
            "eligible": False,
            "reasons": reasons,
            "mapped_event_type": mapped,
        }

    contribution = ADAPTER.convert(envelope)
    contribution_path = ADAPTER.contribution_path(envelope)
    envelope_path = ADAPTER.envelope_path(envelope)
    branch = branch_name(envelope)

    encoded_path = urllib.parse.quote(contribution_path, safe="/")
    existing = request_json(
        "GET",
        repo_url(
            api_base,
            repository,
            f"/contents/{encoded_path}?ref={urllib.parse.quote(base)}",
        ),
        token,
        allow_404=True,
    )
    rendered = json.dumps(contribution, indent=2, ensure_ascii=False) + "\n"
    if existing is not None:
        current = base64.b64decode(existing["content"]).decode()
        if json.loads(current) == contribution:
            return {
                "status": "duplicate",
                "eligible": True,
                "path": contribution_path,
                "message": "identical contribution already exists on base branch",
            }
        raise PublishError(f"{contribution_path} exists with different content")

    ref = request_json(
        "GET",
        repo_url(api_base, repository, f"/git/ref/heads/{base}"),
        token,
    )
    base_sha = ref["object"]["sha"]

    branch_ref = request_json(
        "GET",
        repo_url(
            api_base,
            repository,
            f"/git/ref/heads/{urllib.parse.quote(branch, safe='')}",
        ),
        token,
        allow_404=True,
    )
    if branch_ref is None:
        request_json(
            "POST",
            repo_url(api_base, repository, "/git/refs"),
            token,
            {"ref": f"refs/heads/{branch}", "sha": base_sha},
        )

    owner = repository.split("/", 1)[0]
    pulls = request_json(
        "GET",
        repo_url(
            api_base,
            repository,
            "/pulls?state=open"
            f"&head={urllib.parse.quote(owner + ':' + branch)}"
            f"&base={urllib.parse.quote(base)}",
        ),
        token,
    )
    if pulls:
        return {
            "status": "duplicate",
            "eligible": True,
            "pr_url": pulls[0]["html_url"],
            "branch": branch,
            "message": "open PR already exists",
        }

    def create_file(path: str, body: str, message: str) -> None:
        request_json(
            "PUT",
            repo_url(
                api_base,
                repository,
                f"/contents/{urllib.parse.quote(path, safe='/')}",
            ),
            token,
            {
                "message": message,
                "content": base64.b64encode(body.encode()).decode(),
                "branch": branch,
            },
        )

    create_file(
        contribution_path,
        rendered,
        f"contrib(robotics): {envelope['sensor']['event_key']}",
    )
    create_file(
        envelope_path,
        json.dumps(envelope, indent=2, ensure_ascii=False) + "\n",
        f"provenance(robotics): {envelope['sensor']['event_key']} Sensor Kev envelope",
    )

    pr = request_json(
        "POST",
        repo_url(api_base, repository, "/pulls"),
        token,
        {
            "title": pr_title(envelope),
            "head": branch,
            "base": base,
            "body": pr_body(envelope, contribution_path),
            "draft": False,
            "maintainer_can_modify": True,
        },
    )
    return {
        "status": "created",
        "eligible": True,
        "pr_url": pr["html_url"],
        "pr_number": pr["number"],
        "branch": branch,
        "path": contribution_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument(
        "--repository",
        default=os.getenv("IWM_GITHUB_REPOSITORY", "Azhu9701/industry-world-model"),
    )
    parser.add_argument(
        "--base", default=os.getenv("IWM_GITHUB_BASE_BRANCH", "main")
    )
    parser.add_argument(
        "--api-base", default=os.getenv("GITHUB_API_URL", "https://api.github.com")
    )
    args = parser.parse_args()

    envelope = ADAPTER.load_json(args.input)
    ok, reasons, mapped = ADAPTER.eligibility(envelope)
    preview = {
        "eligible": ok,
        "reasons": reasons,
        "mapped_event_type": mapped,
        "branch": branch_name(envelope),
        "path": ADAPTER.contribution_path(envelope),
        "repository": args.repository,
        "base": args.base,
        "publish": args.publish,
    }

    if not args.publish:
        print(json.dumps({"status": "dry_run", **preview}, ensure_ascii=False))
        return 0 if ok else 3

    token = os.getenv("IWM_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        print(
            "IWM_GITHUB_TOKEN (or GITHUB_TOKEN) is required with --publish",
            file=sys.stderr,
        )
        return 2

    try:
        result = publish(
            envelope,
            token=token,
            repository=args.repository,
            base=args.base,
            api_base=args.api_base,
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except PublishError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
