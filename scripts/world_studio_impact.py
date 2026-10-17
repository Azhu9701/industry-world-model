#!/usr/bin/env python3
"""World Studio WS-01 isolated impact prototype — synthetic fixtures ONLY.

This is a deterministic calculation, NOT a persistence/review/publication
runtime. WS-02 must supply an accepted, versioned canonical change and
durable outbox before this logic can consume production data.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


class FixtureValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FixtureValidationError(message)


def identity(ref: dict[str, Any]) -> tuple[str, str, str, int] | None:
    """Never match by bare claim ID, display name, or latest value."""
    world, pack, claim_id, version = (
        ref.get("world"), ref.get("pack"), ref.get("claimId"), ref.get("version")
    )
    if not (isinstance(world, str) and world
            and isinstance(pack, str) and pack
            and isinstance(claim_id, str) and claim_id
            and type(version) is int and version > 0):
        return None
    return world, pack, claim_id, version


def impact_plan(fixture: dict[str, Any]) -> dict[str, Any]:
    """Plan review tasks with stable keys; perform no writes or side effects."""
    require(fixture.get("synthetic") is True,
            "Prototype rejects non-synthetic input; no production data")
    change = fixture.get("change")
    require(isinstance(change, dict), "Missing canonical change")
    old, new = change.get("oldClaim"), change.get("newClaim")
    require(isinstance(old, dict) and isinstance(new, dict),
            "Both old and new claim versions are required")
    require(new.get("supersedes") == [old.get("id")]
            and type(new.get("version")) is int
            and type(old.get("version")) is int
            and new["version"] == old["version"] + 1,
            "Claim version/supersession mismatch")
    require(new.get("status") == "verified" and old.get("status") == "superseded",
            "Prototype only models an accepted supersession, not proposals")
    require(old.get("evidenceIds") and new.get("evidenceIds"),
            "Evidence references must be retained")
    world, pack, key = fixture.get("world"), fixture.get("pack"), change.get("changeKey")
    require(all(isinstance(value, str) and value for value in (world, pack, key)),
            "World, pack and change key are mandatory")
    expected_identity = identity({
        "world": world, "pack": pack, "claimId": old.get("id"),
        "version": old.get("version"),
    })
    require(expected_identity is not None, "Invalid old claim identity")
    contents = fixture.get("contents")
    require(isinstance(contents, list), "Content registry must be a list")
    seen: set[str] = set()
    tasks: list[dict[str, Any]] = []
    unaffected: list[str] = []
    for item in contents:
        require(isinstance(item, dict), "Invalid content record")
        content_id, revision = item.get("id"), item.get("revision")
        require(isinstance(content_id, str) and content_id not in seen and content_id,
                "Duplicate/empty content ID")
        seen.add(content_id)
        require(type(revision) is int and revision > 0, "Invalid content revision")
        state = item.get("state")
        require(state in ("draft", "published"), "Unknown content state must be reviewed")
        approved_rev = item.get("approvedRevision")
        require(approved_rev is None or (type(approved_rev) is int and 0 < approved_rev <= revision),
                "Invalid approval revision")
        refs = item.get("factReferences")
        require(isinstance(refs, list) and all(isinstance(r, dict) for r in refs),
                "Invalid fact references")
        if not any(identity(ref) == expected_identity for ref in refs):
            unaffected.append(content_id)
            continue
        action = "re_review_draft" if state == "draft" else "review_published_correction"
        tasks.append({
            "taskKey": f"{key}:{content_id}:revision-{revision}",
            "contentId": content_id, "contentRevision": revision,
            "action": action, "approvalInvalidated": state == "draft" and approved_rev == revision,
            "reason": {"world": world, "pack": pack,
                       "claimId": old["id"], "claimVersion": old["version"]},
            "status": "needs_editorial_review",
            "draftCreated": False, "published": False,
        })
    tasks.sort(key=lambda t: t["contentId"])
    return {
        "changeKey": key,
        "affectedContentIds": [task["contentId"] for task in tasks],
        "unaffectedContentIds": sorted(unaffected),
        "tasks": tasks,
        "unregisteredContentCoverage": "unknown",
        "persisted": False,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/world_studio_impact.py <synthetic-fixture.json>", file=sys.stderr)
        return 2
    try:
        obj = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        result = impact_plan(obj)
    except (OSError, ValueError, TypeError) as exc:
        print(f"impact planning refused: {type(exc).__name__}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
