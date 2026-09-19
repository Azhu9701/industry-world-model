#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "protocol" / "schemas"

SCHEMA_FILES = {
    "contribution": "contribution.schema.json",
    "entity": "entity.schema.json",
    "claim": "claim.schema.json",
    "relation": "relation.schema.json",
    "event": "event.schema.json",
    "evidence": "evidence.schema.json",
    "snapshot": "snapshot.schema.json",
}


class ValidationFailure(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        raise ValidationFailure(f"{path}: invalid JSON: {exc}") from exc


def load_schema(kind: str) -> dict[str, Any]:
    path = SCHEMA_DIR / SCHEMA_FILES[kind]
    schema = load_json(path)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_schema(instance: Any, kind: str, path: Path, schemas: dict[str, dict[str, Any]]) -> None:
    validator = Draft202012Validator(schemas[kind])
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    if errors:
        rendered = []
        for err in errors:
            pointer = ".".join(str(p) for p in err.absolute_path) or "<root>"
            rendered.append(f"{path}: {kind} schema error at {pointer}: {err.message}")
        raise ValidationFailure("\n".join(rendered))


def load_pack(pack_name: str) -> dict[str, Any]:
    path = ROOT / "packs" / pack_name / "domain.yaml"
    if not path.is_file():
        raise ValidationFailure(f"unknown pack {pack_name!r}: {path} does not exist")
    try:
        pack = yaml.safe_load(path.read_text())
    except Exception as exc:
        raise ValidationFailure(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(pack, dict):
        raise ValidationFailure(f"{path}: pack must be an object")
    return pack


def validate_packet(path: Path, packet: dict[str, Any], schemas: dict[str, dict[str, Any]]) -> None:
    validate_schema(packet, "contribution", path, schemas)
    pack = load_pack(packet["pack"])

    entities = packet["entities"]
    claims = packet["claims"]
    relations = packet["relations"]
    events = packet["events"]
    evidences = packet["evidence"]

    for item in entities:
        validate_schema(item, "entity", path, schemas)
    for item in claims:
        validate_schema(item, "claim", path, schemas)
    for item in relations:
        validate_schema(item, "relation", path, schemas)
    for item in events:
        validate_schema(item, "event", path, schemas)
    for item in evidences:
        validate_schema(item, "evidence", path, schemas)

    all_items = entities + claims + relations + events + evidences
    ids = [item["id"] for item in all_items]
    duplicate_ids = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
    if duplicate_ids:
        raise ValidationFailure(f"{path}: duplicate ids: {', '.join(duplicate_ids)}")

    entity_types = set((pack.get("entities") or {}).keys())
    claim_predicates = set(pack.get("claims") or [])
    event_types = set(pack.get("events") or [])
    relation_rules = {
        (rule["subject"], rule["predicate"], rule["object"])
        for rule in (pack.get("relations") or [])
    }

    for entity in entities:
        if entity["entity_type"] not in entity_types:
            raise ValidationFailure(
                f"{path}: entity type {entity['entity_type']!r} is not declared by pack {packet['pack']!r}"
            )

    for claim in claims:
        if claim["status"] != "proposed":
            raise ValidationFailure(f"{path}: incoming claim {claim['id']} must have status='proposed'")
        if claim["predicate"] not in claim_predicates:
            raise ValidationFailure(
                f"{path}: claim predicate {claim['predicate']!r} is not declared by pack {packet['pack']!r}"
            )
        if claim["subject"]["entity_type"] not in entity_types:
            raise ValidationFailure(
                f"{path}: claim {claim['id']} references unknown entity type {claim['subject']['entity_type']!r}"
            )

    for relation in relations:
        if relation["status"] != "proposed":
            raise ValidationFailure(f"{path}: incoming relation {relation['id']} must have status='proposed'")
        rule = (
            relation["subject"]["entity_type"],
            relation["predicate"],
            relation["object"]["entity_type"],
        )
        if rule not in relation_rules:
            raise ValidationFailure(
                f"{path}: relation rule {rule[0]}:{rule[1]}:{rule[2]} is not declared by pack {packet['pack']!r}"
            )

    for event in events:
        if event["status"] != "proposed":
            raise ValidationFailure(f"{path}: incoming event {event['id']} must have status='proposed'")
        if event["event_type"] not in event_types:
            raise ValidationFailure(
                f"{path}: event type {event['event_type']!r} is not declared by pack {packet['pack']!r}"
            )
        for participant in event.get("participants", []):
            if participant["entity"]["entity_type"] not in entity_types:
                raise ValidationFailure(
                    f"{path}: event {event['id']} participant references unknown entity type "
                    f"{participant['entity']['entity_type']!r}"
                )

    fact_by_id = {item["id"]: item for item in claims + relations + events}
    evidence_by_id = {item["id"]: item for item in evidences}

    for fact in claims + relations + events:
        for evidence_id in fact["evidence_ids"]:
            evidence = evidence_by_id.get(evidence_id)
            if evidence is None:
                raise ValidationFailure(f"{path}: {fact['id']} references missing evidence {evidence_id}")
            if evidence["target"]["id"] != fact["id"]:
                raise ValidationFailure(
                    f"{path}: {evidence_id} targets {evidence['target']['id']}, not {fact['id']}"
                )

    expected_kind = {}
    expected_kind.update({item["id"]: "claim" for item in claims})
    expected_kind.update({item["id"]: "relation" for item in relations})
    expected_kind.update({item["id"]: "event" for item in events})

    for evidence in evidences:
        target_id = evidence["target"]["id"]
        if target_id not in fact_by_id:
            raise ValidationFailure(f"{path}: evidence {evidence['id']} targets missing fact {target_id}")
        if evidence["target"]["kind"] != expected_kind[target_id]:
            raise ValidationFailure(
                f"{path}: evidence {evidence['id']} target kind {evidence['target']['kind']!r} "
                f"does not match {expected_kind[target_id]!r}"
            )


def validate_snapshot(path: Path, snapshot: dict[str, Any], schemas: dict[str, dict[str, Any]]) -> None:
    validate_schema(snapshot, "snapshot", path, schemas)
    load_pack(snapshot["pack"])


def discover() -> tuple[list[Path], list[Path]]:
    contributions = sorted((ROOT / "contributions").glob("**/contribution.json"))
    examples = sorted((ROOT / "examples").glob("**/contribution.json"))
    snapshots = sorted((ROOT / "examples").glob("**/snapshot.json"))
    return contributions + examples, snapshots


def main() -> int:
    try:
        schemas = {kind: load_schema(kind) for kind in SCHEMA_FILES}
        packets, snapshots = discover()
        if not packets:
            raise ValidationFailure("no contribution examples found")
        for path in packets:
            packet = load_json(path)
            validate_packet(path, packet, schemas)
            print(f"ok contribution: {path.relative_to(ROOT)}")
        for path in snapshots:
            snapshot = load_json(path)
            validate_snapshot(path, snapshot, schemas)
            print(f"ok snapshot: {path.relative_to(ROOT)}")
        print(
            f"validated {len(packets)} contribution packet(s), "
            f"{len(snapshots)} snapshot(s), and {len(schemas)} schema(s)"
        )
        return 0
    except ValidationFailure as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
