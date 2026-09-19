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
SCHEMA = ROOT / "protocol" / "adapters" / "sensor-kev-event.schema.json"


class BridgeError(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        raise BridgeError(f"{path}: invalid JSON: {exc}") from exc


def validate_envelope(envelope: dict[str, Any]) -> None:
    schema = load_json(SCHEMA)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(envelope),
        key=lambda e: list(e.absolute_path),
    )
    if errors:
        lines = []
        for error in errors:
            pointer = ".".join(str(part) for part in error.absolute_path) or "<root>"
            lines.append(f"sensor-kev schema error at {pointer}: {error.message}")
        raise BridgeError("\n".join(lines))


def slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "item"


def digest(value: str, length: int = 10) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:length]


def map_source_type(value: str) -> str:
    return {
        "official": "first_party",
        "government": "government",
        "paper": "academic",
        "wire": "media",
        "industry_media": "media",
        "other": "other",
    }[value]


def map_event_type(decision: dict[str, Any]) -> str | None:
    event_type = decision["event_type"]
    stage = decision["commercialization_stage"]
    if event_type == "funding":
        return "funding"
    if event_type == "product" and stage == "launch":
        return "product_release"
    if event_type == "product" and stage == "mass_production":
        return "mass_production"
    if event_type in {"product", "case", "market"} and stage == "deployment":
        return "deployment"
    return None


def eligibility(envelope: dict[str, Any]) -> tuple[bool, list[str], str | None]:
    validate_envelope(envelope)
    sensor = envelope["sensor"]
    decision = envelope["kev"]["decision_packet"]
    reasons: list[str] = []

    if sensor["verification_status"] != "verified":
        reasons.append("sensor_not_verified")
    if not decision["is_event"]:
        reasons.append("kev_not_event")
    if not decision["timeline_worthy"]:
        reasons.append("not_timeline_worthy")
    if decision["needs_second_source"]:
        reasons.append("needs_second_source")

    source_urls = {source["url"] for source in sensor["sources"]}
    if len(source_urls) < 2:
        reasons.append("fewer_than_two_sources")

    for index, fact in enumerate(sensor["facts"]):
        if any(url not in source_urls for url in fact["source_urls"]):
            reasons.append(f"fact_{index}_references_unknown_source")

    mapped = map_event_type(decision)
    if mapped is None:
        reasons.append("ontology_event_mapping_requires_review")

    return not reasons, reasons, mapped


def contribution_path(envelope: dict[str, Any]) -> str:
    sensor = envelope["sensor"]
    return (
        f"contributions/{slug(envelope['pack'])}/"
        f"{sensor['event_date']}-{slug(sensor['event_key'])}/contribution.json"
    )


def envelope_path(envelope: dict[str, Any]) -> str:
    return contribution_path(envelope).replace(
        "contribution.json", "sensor-kev-envelope.json"
    )


def convert(envelope: dict[str, Any]) -> dict[str, Any]:
    ok, reasons, mapped = eligibility(envelope)
    if not ok or mapped is None:
        raise BridgeError(
            "automatic contribution gate rejected envelope: " + ",".join(reasons)
        )

    sensor = envelope["sensor"]
    kev = envelope["kev"]
    decision = kev["decision_packet"]
    observed_at = envelope["observed_at"]
    event_id = f"event:{slug(sensor['event_key'])}"

    facts_by_source: dict[str, list[int]] = {}
    for index, fact in enumerate(sensor["facts"]):
        for url in fact["source_urls"]:
            facts_by_source.setdefault(url, []).append(index)

    evidence = []
    evidence_ids = []
    for source in sensor["sources"]:
        evidence_id = (
            f"evidence:{slug(event_id.replace(':', '-'))}-{digest(source['url'], 8)}"
        )
        evidence_ids.append(evidence_id)
        src: dict[str, Any] = {
            "url": source["url"],
            "title": source["title"],
            "source_type": map_source_type(source["source_type"]),
            "accessed_at": observed_at,
        }
        if source.get("publisher") is not None:
            src["publisher"] = source["publisher"]
        if source.get("published_at") is not None:
            src["published_at"] = source["published_at"]

        item: dict[str, Any] = {
            "id": evidence_id,
            "target": {"kind": "event", "id": event_id},
            "source": src,
            "captured_at": observed_at,
            "stance": "supports",
        }
        indexes = facts_by_source.get(source["url"], [])
        if indexes:
            item["locator"] = "sensor.facts[" + ",".join(map(str, indexes)) + "]"
        evidence.append(item)

    classification = {
        "new_event": "NEW_EVENT",
        "follow_up": "FOLLOW_UP",
        "enrichment": "ENRICHMENT",
    }[sensor["event_class"]]

    event = {
        "id": event_id,
        "event_type": mapped,
        "event_key": sensor["event_key"],
        "title": sensor["title"],
        "occurred_on": sensor["event_date"],
        "date_precision": "day",
        "classification": classification,
        "status": "proposed",
        "observed_at": observed_at,
        "evidence_ids": evidence_ids,
        "attributes": {
            "sensor": {
                "verification_status": sensor["verification_status"],
                "history_link": sensor["history_link"],
                "predecessor_event_id": sensor.get("predecessor_event_id"),
                "relation": sensor.get("relation"),
                "history_reason": sensor.get("history_reason"),
                "facts": sensor["facts"],
                "caveats": sensor.get("caveats", []),
                "related_entities": sensor["related_entities"],
                "editorial_significance": sensor["significance"],
            },
            "kev": {
                "model": kev["model"],
                "contract_version": kev["contract_version"],
                "contract_sha256": kev.get("contract_sha256"),
                "model_sha256": kev.get("model_sha256"),
                "decision_packet": decision,
            },
        },
    }

    return {
        "protocol_version": "0.3.0",
        "contribution_id": (
            f"contrib:{slug(envelope['pack'])}-{slug(envelope['idempotency_key'])}"
        ),
        "pack": envelope["pack"],
        "created_at": observed_at,
        "contributor": envelope["contributor"],
        "idempotency_key": envelope["idempotency_key"],
        "summary": sensor["title"],
        "metadata": {
            "adapter": {
                "name": "sensor-kev-event",
                "version": "0.1.0",
                "sensor_contract": "emibot-pi.VerifierSchema",
                "kev_contract": kev["contract_version"],
            },
            "automation": {
                "eligible": True,
                "gate": [
                    "sensor_verified",
                    "two_independent_sources",
                    "kev_is_event",
                    "timeline_worthy",
                    "no_second_source_needed",
                    "deterministic_ontology_mapping",
                ],
                "canonical_write": False,
                "auto_merge": False,
            },
        },
        "entities": [],
        "claims": [],
        "relations": [],
        "events": [event],
        "evidence": evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        envelope = load_json(args.input)
        ok, reasons, mapped = eligibility(envelope)
        if args.check:
            print(
                json.dumps(
                    {
                        "eligible": ok,
                        "reasons": reasons,
                        "mapped_event_type": mapped,
                    },
                    ensure_ascii=False,
                )
            )
            return 0 if ok else 3

        rendered = json.dumps(convert(envelope), indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered)
        else:
            sys.stdout.write(rendered)
        return 0
    except BridgeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
