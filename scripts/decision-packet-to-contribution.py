#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
INPUT_SCHEMA = ROOT / "protocol" / "adapters" / "decision-packet.schema.json"


class AdapterError(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        raise AdapterError(f"{path}: invalid JSON: {exc}") from exc


def validate_input(packet: dict[str, Any]) -> None:
    schema = load_json(INPUT_SCHEMA)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(packet), key=lambda e: list(e.absolute_path))
    if errors:
        rendered = []
        for error in errors:
            pointer = ".".join(str(part) for part in error.absolute_path) or "<root>"
            rendered.append(f"decision packet schema error at {pointer}: {error.message}")
        raise AdapterError("\n".join(rendered))


def slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "item"


def digest(value: Any, length: int = 10) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()[:length]


def source_for_evidence(source: dict[str, Any]) -> dict[str, Any]:
    allowed = (
        "url",
        "title",
        "publisher",
        "source_type",
        "published_at",
        "accessed_at",
        "license",
    )
    return {key: source[key] for key in allowed if key in source}


def evidence_for(
    *,
    target_kind: str,
    target_id: str,
    locator: str | None,
    source: dict[str, Any],
    observed_at: str,
) -> dict[str, Any]:
    source_hash = digest(source["url"], 8)
    evidence_id = (
        f"evidence:{slug(target_id.replace(':', '-'))}-{source_hash}"
    )
    item: dict[str, Any] = {
        "id": evidence_id,
        "target": {"kind": target_kind, "id": target_id},
        "source": source_for_evidence(source),
        "captured_at": observed_at,
        "stance": "supports",
    }
    if locator:
        item["locator"] = locator
    return item


def convert(packet: dict[str, Any]) -> dict[str, Any]:
    validate_input(packet)

    decision = packet["decision"]
    extraction = packet["extraction"]
    observed_at = packet["observed_at"]
    source = packet["source"]

    extracted_event = extraction.get("event")
    if decision["is_event"] and extracted_event is None:
        raise AdapterError("decision.is_event=true requires extraction.event")
    if not decision["is_event"] and extracted_event is not None:
        raise AdapterError("extraction.event is present but decision.is_event=false")
    if extracted_event is not None and decision.get("event_type"):
        if extracted_event["event_type"] != decision["event_type"]:
            raise AdapterError(
                "decision.event_type does not match extraction.event.event_type"
            )

    entities = []
    for item in extraction.get("entities", []):
        entity = {
            "id": f"entity:{slug(item['entity_type'])}-{slug(item['entity_key'])}",
            "entity_type": item["entity_type"],
            "entity_key": item["entity_key"],
            "name": item["name"],
        }
        if item.get("description") is not None:
            entity["description"] = item["description"]
        if "aliases" in item:
            entity["aliases"] = item["aliases"]
        if "attributes" in item:
            entity["attributes"] = item["attributes"]
        entities.append(entity)

    claims = []
    relations = []
    events = []
    evidence = []

    for item in extraction.get("claims", []):
        claim_id = (
            f"claim:{slug(item['subject']['entity_key'])}-"
            f"{slug(item['predicate'])}-{digest(item['value'])}"
        )
        ev = evidence_for(
            target_kind="claim",
            target_id=claim_id,
            locator=item.get("locator"),
            source=source,
            observed_at=observed_at,
        )
        claim: dict[str, Any] = {
            "id": claim_id,
            "subject": item["subject"],
            "predicate": item["predicate"],
            "value": item["value"],
            "status": "proposed",
            "observed_at": observed_at,
            "evidence_ids": [ev["id"]],
        }
        for key in ("unit", "confidence", "valid_from", "valid_to"):
            if key in item:
                claim[key] = item[key]
        claims.append(claim)
        evidence.append(ev)

    for item in extraction.get("relations", []):
        relation_id = (
            f"relation:{slug(item['subject']['entity_key'])}-"
            f"{slug(item['predicate'])}-{slug(item['object']['entity_key'])}"
        )
        ev = evidence_for(
            target_kind="relation",
            target_id=relation_id,
            locator=item.get("locator"),
            source=source,
            observed_at=observed_at,
        )
        relation: dict[str, Any] = {
            "id": relation_id,
            "subject": item["subject"],
            "predicate": item["predicate"],
            "object": item["object"],
            "status": "proposed",
            "observed_at": observed_at,
            "evidence_ids": [ev["id"]],
        }
        for key in ("valid_from", "valid_to", "attributes"):
            if key in item:
                relation[key] = item[key]
        relations.append(relation)
        evidence.append(ev)

    if extracted_event is not None:
        event_id = f"event:{slug(extracted_event['event_key'])}"
        ev = evidence_for(
            target_kind="event",
            target_id=event_id,
            locator=extracted_event.get("locator"),
            source=source,
            observed_at=observed_at,
        )
        event: dict[str, Any] = {
            "id": event_id,
            "event_type": extracted_event["event_type"],
            "event_key": extracted_event["event_key"],
            "title": extracted_event["title"],
            "classification": extracted_event.get("classification", "NEW_EVENT"),
            "status": "proposed",
            "observed_at": observed_at,
            "evidence_ids": [ev["id"]],
        }
        for key in (
            "summary",
            "occurred_on",
            "occurred_end",
            "date_precision",
            "participants",
            "attributes",
        ):
            if key in extracted_event:
                event[key] = extracted_event[key]
        events.append(event)
        evidence.append(ev)

    review_flags = []
    if decision.get("needs_second_source"):
        review_flags.append("needs_second_source")
    if not decision.get("timeline_worthy", False) and extracted_event is not None:
        review_flags.append("not_timeline_worthy")

    return {
        "protocol_version": "0.3.0",
        "contribution_id": (
            f"contrib:{slug(packet['pack'])}-{slug(packet['idempotency_key'])}"
        ),
        "pack": packet["pack"],
        "created_at": observed_at,
        "contributor": packet["contributor"],
        "idempotency_key": packet["idempotency_key"],
        "summary": extraction["summary"],
        "metadata": {
            "adapter": {
                "name": "decision-packet-to-contribution",
                "version": "0.1.0",
                "input_version": packet["decision_packet_version"],
            },
            "decision": decision,
            "review_flags": review_flags,
        },
        "entities": entities,
        "claims": claims,
        "relations": relations,
        "events": events,
        "evidence": evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert an AIMAN Decision Packet into an IWM v0.3 Contribution Packet."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", "-o", type=Path)
    args = parser.parse_args()

    try:
        packet = load_json(args.input)
        contribution = convert(packet)
        rendered = json.dumps(contribution, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered)
        else:
            sys.stdout.write(rendered)
        return 0
    except AdapterError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
