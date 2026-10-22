from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCHEMA_VERSION = "aiman.openbot_candidate.v0"
SUPPORTED_RECORD_TYPES = {"dataset", "model"}
ALLOWED_HINTS = {"release_date", "license", "repository"}
OPENBOT_HOSTS = {"openbot.ai", "www.openbot.ai"}

SOURCE_PRIORITY = {
    "official": 0,
    "project_page": 1,
    "repository": 2,
    "paper": 3,
    "huggingface": 4,
    "dataset_page": 5,
    "model_page": 5,
    "other": 9,
}
SUPPORTED_SOURCE_TYPES = set(SOURCE_PRIORITY)


class SensorError(ValueError):
    pass


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SensorError(f"{field} must be a non-empty string")
    return value.strip()


def _http_url(value: Any, field: str) -> str:
    url = _require_string(value, field)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SensorError(f"{field} must be an http(s) URL")
    return url


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def _identity_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in value if character.isalnum())


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    if slug:
        return slug[:80]
    digest = hashlib.sha256(value.encode()).hexdigest()[:16]
    return f"entity-{digest}"


def _fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _normalize_source(source: Any, index: int) -> dict[str, Any]:
    if not isinstance(source, dict):
        raise SensorError(f"upstream_sources[{index}] must be an object")
    url = _http_url(source.get("url"), f"upstream_sources[{index}].url")
    title = _require_string(source.get("title"), f"upstream_sources[{index}].title")
    source_type = source.get("source_type", "other")
    if source_type not in SUPPORTED_SOURCE_TYPES:
        raise SensorError(
            f"upstream_sources[{index}].source_type must be one of "
            + ", ".join(sorted(SUPPORTED_SOURCE_TYPES))
        )

    normalized = {
        "url": url,
        "title": title,
        "source_type": source_type,
    }
    supports = source.get("supports") or {}
    if not isinstance(supports, dict):
        raise SensorError(f"upstream_sources[{index}].supports must be an object")
    normalized["supports"] = {
        key: value
        for key, value in supports.items()
        if key in ALLOWED_HINTS and value is not None and value != ""
    }
    for key in ("publisher", "published_at", "excerpt"):
        value = source.get(key)
        if value is not None:
            normalized[key] = _require_string(value, f"upstream_sources[{index}].{key}")
    normalized["discovery_only"] = _host(url) in OPENBOT_HOSTS
    return normalized


def normalize_record(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise SensorError("record must be an object")

    record_type = _require_string(record.get("record_type"), "record_type").casefold()
    if record_type not in SUPPORTED_RECORD_TYPES:
        raise SensorError(f"record_type must be one of {sorted(SUPPORTED_RECORD_TYPES)}")

    name = _require_string(record.get("name"), "name")
    record_url = _http_url(record.get("record_url"), "record_url")
    if _host(record_url) not in OPENBOT_HOSTS:
        raise SensorError("record_url must point to openbot.ai")

    record_id = record.get("record_id")
    if record_id is not None:
        record_id = _require_string(record_id, "record_id")

    aliases: list[str] = []
    seen_aliases = {_identity_text(name)}
    for index, alias in enumerate(record.get("aliases") or []):
        alias = _require_string(alias, f"aliases[{index}]")
        identity = _identity_text(alias)
        if identity and identity not in seen_aliases:
            aliases.append(alias)
            seen_aliases.add(identity)

    upstream_sources = [
        _normalize_source(source, index)
        for index, source in enumerate(record.get("upstream_sources") or [])
    ]

    raw_hints = record.get("hints") or {}
    if not isinstance(raw_hints, dict):
        raise SensorError("hints must be an object")
    hints = {
        key: value
        for key, value in raw_hints.items()
        if key in ALLOWED_HINTS and value is not None and value != ""
    }
    unsupported_hints = {
        key: value
        for key, value in raw_hints.items()
        if key not in ALLOWED_HINTS and value is not None and value != ""
    }

    external_assessment = record.get("external_assessment")
    if external_assessment is not None and not isinstance(external_assessment, dict):
        raise SensorError("external_assessment must be an object when present")

    fingerprint_input = {
        "provider": "openbot",
        "record_type": record_type,
        "record_id": record_id,
        "record_url": record_url,
        "name": name,
        "aliases": aliases,
        "upstream_sources": upstream_sources,
        "hints": hints,
        "unsupported_hints": unsupported_hints,
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "provider": "openbot",
        "status": "candidate",
        "canonical": False,
        "record_type": record_type,
        "record_id": record_id,
        "record_url": record_url,
        "name": name,
        "aliases": aliases,
        "upstream_sources": upstream_sources,
        "hints": hints,
        "unsupported_hints": unsupported_hints,
        "external_assessment": external_assessment,
        "observed_at": record.get("observed_at"),
        "last_seen_at": record.get("last_seen_at"),
        "candidate_fingerprint": _fingerprint(fingerprint_input),
    }


def normalize_batch(records: list[Any]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str], dict[str, Any]] = {}

    for record in records:
        candidate = normalize_record(record)
        provider_key = candidate["record_id"] or candidate["record_url"]
        key = (candidate["record_type"], provider_key)
        previous = by_key.get(key)
        if previous is None:
            by_key[key] = candidate
            candidates.append(candidate)
            continue
        if previous["candidate_fingerprint"] == candidate["candidate_fingerprint"]:
            duplicates.append(
                {
                    "record_type": candidate["record_type"],
                    "provider_key": provider_key,
                    "candidate_fingerprint": candidate["candidate_fingerprint"],
                }
            )
        else:
            conflicts.append(
                {
                    "record_type": candidate["record_type"],
                    "provider_key": provider_key,
                    "reason": "same OpenBot record key produced different candidate content",
                    "candidate_fingerprints": sorted(
                        {
                            previous["candidate_fingerprint"],
                            candidate["candidate_fingerprint"],
                        }
                    ),
                }
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "candidates": candidates,
        "duplicates": duplicates,
        "conflicts": conflicts,
    }


def _entity_identity_values(entity: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for key in ("name", "entityKey", "entity_key"):
        value = entity.get(key)
        if isinstance(value, str) and value.strip():
            values.add(_identity_text(value))

    aliases = entity.get("aliases")
    if not isinstance(aliases, list):
        attributes = entity.get("attributes")
        aliases = attributes.get("aliases") if isinstance(attributes, dict) else None
    if isinstance(aliases, list):
        for alias in aliases:
            if isinstance(alias, str) and alias.strip():
                values.add(_identity_text(alias))
    return values


def resolve_identity(
    candidate: dict[str, Any], existing_entities: list[dict[str, Any]]
) -> dict[str, Any]:
    candidate_values = {
        _identity_text(candidate["name"]),
        *(_identity_text(alias) for alias in candidate.get("aliases", [])),
    }
    if candidate.get("record_id"):
        candidate_values.add(_identity_text(candidate["record_id"]))
    candidate_values.discard("")

    matches: list[dict[str, Any]] = []
    for entity in existing_entities:
        entity_type = entity.get("entityType", entity.get("entity_type"))
        if entity_type != candidate["record_type"]:
            continue
        if candidate_values & _entity_identity_values(entity):
            matches.append(entity)

    if len(matches) == 1:
        return {
            "status": "existing",
            "reason": "exact normalized identity match",
            "entity": matches[0],
            "matches": [matches[0]],
        }
    if len(matches) > 1:
        return {
            "status": "review_required",
            "reason": "multiple canonical entities match the same OpenBot identity",
            "entity": None,
            "matches": matches,
        }
    return {
        "status": "new",
        "reason": "no exact canonical identity match",
        "entity": None,
        "matches": [],
    }


def _trusted_sources(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    sources = [
        source
        for source in candidate.get("upstream_sources", [])
        if not source.get("discovery_only")
    ]
    return sorted(
        sources,
        key=lambda source: (
            SOURCE_PRIORITY.get(source.get("source_type", "other"), 99),
            source["url"],
        ),
    )


def _source_for_predicate(
    candidate: dict[str, Any], predicate: str, value: Any
) -> dict[str, Any] | None:
    sources = _trusted_sources(candidate)
    for source in sources:
        if source.get("supports", {}).get(predicate) == value:
            return source

    if predicate == "repository" and isinstance(value, str):
        for source in sources:
            if source.get("source_type") == "repository" and source["url"].rstrip("/") == value.rstrip("/"):
                return source
    return None


def _runtime_source(source: dict[str, Any]) -> dict[str, Any]:
    result = {
        "url": source["url"],
        "title": source["title"],
    }
    for key in ("publisher", "published_at", "excerpt"):
        if source.get(key):
            result[key] = source[key]
    return result


def _proposal_key(candidate: dict[str, Any], kind: str, suffix: str) -> str:
    raw = f"openbot:{candidate['candidate_fingerprint']}:{kind}:{suffix}"
    return f"openbot-{hashlib.sha256(raw.encode()).hexdigest()[:40]}"


def build_plan(
    candidate: dict[str, Any],
    existing_entities: list[dict[str, Any]],
    *,
    pack: str = "robotics",
) -> dict[str, Any]:
    resolution = resolve_identity(candidate, existing_entities)
    proposals: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []

    if resolution["status"] == "review_required":
        return {
            "candidate": candidate,
            "resolution": resolution,
            "proposals": [],
            "gaps": [
                {
                    "kind": "identity_conflict",
                    "message": "manual review required before any canonical proposal",
                }
            ],
            "external_assessment": candidate.get("external_assessment"),
        }

    if resolution["status"] == "existing":
        entity = resolution["entity"]
        entity_key = entity.get("entityKey", entity.get("entity_key"))
        if not isinstance(entity_key, str) or not entity_key:
            gaps.append(
                {
                    "kind": "identity_incomplete",
                    "message": "matched entity has no entity key; claims were not proposed",
                }
            )
            return {
                "candidate": candidate,
                "resolution": resolution,
                "proposals": [],
                "gaps": gaps,
                "external_assessment": candidate.get("external_assessment"),
            }
    else:
        entity_key = _slug(candidate["name"])
        proposals.append(
            {
                "pack": pack,
                "kind": "entity",
                "payload": {
                    "entity_type": candidate["record_type"],
                    "entity_key": entity_key,
                    "name": candidate["name"],
                    "aliases": candidate.get("aliases", []),
                    "attributes": {
                        "discovered_via": "openbot",
                        "openbot_record_id": candidate.get("record_id"),
                        "openbot_record_url": candidate["record_url"],
                        "candidate_fingerprint": candidate["candidate_fingerprint"],
                    },
                },
                "idempotency_key": _proposal_key(candidate, "entity", entity_key),
            }
        )

    for predicate, value in candidate.get("hints", {}).items():
        source = _source_for_predicate(candidate, predicate, value)
        if source is None:
            gaps.append(
                {
                    "kind": "missing_upstream_evidence",
                    "predicate": predicate,
                    "value": value,
                    "message": "no upstream source explicitly supports this exact field value",
                }
            )
            continue

        proposals.append(
            {
                "pack": pack,
                "kind": "claim",
                "payload": {
                    "subject_type": candidate["record_type"],
                    "subject_key": entity_key,
                    "predicate": predicate,
                    "value": value,
                    "status": "proposed",
                    "metadata": {
                        "discovered_via": "openbot",
                        "openbot_record_url": candidate["record_url"],
                        "candidate_fingerprint": candidate["candidate_fingerprint"],
                    },
                },
                "source": _runtime_source(source),
                "idempotency_key": _proposal_key(candidate, "claim", predicate),
            }
        )

    for predicate, value in candidate.get("unsupported_hints", {}).items():
        gaps.append(
            {
                "kind": "unsupported_hint",
                "predicate": predicate,
                "value": value,
                "message": "hint is preserved for review but is outside the current robotics pack contract",
            }
        )

    return {
        "candidate": candidate,
        "resolution": resolution,
        "proposals": proposals,
        "gaps": gaps,
        "external_assessment": candidate.get("external_assessment"),
    }


def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize OpenBot discovery records into AIMAN proposal plans."
    )
    parser.add_argument("records", help="JSON file containing a list or {'records': [...]} object")
    parser.add_argument(
        "--entities",
        help="Optional AIMAN entity list JSON, either a list or {'items': [...]} object",
    )
    parser.add_argument("--pack", default="robotics")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = _load_json(args.records)
    records = payload.get("records") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise SensorError("records input must be a list or an object with a records list")

    entity_payload = _load_json(args.entities) if args.entities else []
    entities = entity_payload.get("items") if isinstance(entity_payload, dict) else entity_payload
    if not isinstance(entities, list):
        raise SensorError("entities input must be a list or an object with an items list")

    batch = normalize_batch(records)
    output = {
        **batch,
        "plans": [
            build_plan(candidate, entities, pack=args.pack)
            for candidate in batch["candidates"]
        ],
    }
    print(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
