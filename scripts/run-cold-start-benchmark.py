#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = ROOT / "benchmarks" / "cold-start" / "cases" / "robot-product-release-v0.1.json"
REFERENCE_DISCOVERY = ROOT / "benchmarks" / "cold-start" / "fixtures" / "reference-discovery.json"
REFERENCE_CONTRIBUTION = ROOT / "benchmarks" / "cold-start" / "fixtures" / "reference-contribution.json"
VALIDATOR_PATH = ROOT / "scripts" / "validate-contributions.py"

ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")


class BenchmarkError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise BenchmarkError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise BenchmarkError(f"{path}: expected a JSON object")
    return value


def normalize_path(value: str) -> str:
    return value.strip().removeprefix("./")


def extract_json_object(text: str) -> dict[str, Any]:
    clean = ANSI_RE.sub("", text).strip()
    try:
        value = json.loads(clean)
        if isinstance(value, dict):
            return value
    except Exception:
        pass

    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", clean):
        try:
            value, _ = decoder.raw_decode(clean[match.start() :])
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    raise BenchmarkError("model output did not contain a parseable JSON object")


def load_protocol_validator() -> Any:
    spec = importlib.util.spec_from_file_location("iwm_validate_contributions", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise BenchmarkError(f"cannot load protocol validator from {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def protocol_validation(packet: dict[str, Any]) -> tuple[bool, str]:
    try:
        module = load_protocol_validator()
        schemas = {kind: module.load_schema(kind) for kind in module.SCHEMA_FILES}
        module.validate_packet(Path("<cold-start-benchmark>"), packet, schemas)
        return True, "packet passes v0.3 schema, pack, status, and evidence-reference validation"
    except ModuleNotFoundError as exc:
        return False, f"protocol validator dependency missing: {exc}"
    except Exception as exc:
        return False, str(exc)


def check(
    check_id: str,
    passed: bool,
    detail: str,
    *,
    weight: int,
    critical: bool = False,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "passed": bool(passed),
        "weight": weight,
        "critical": critical,
        "detail": detail,
    }


def entity_ref(item: dict[str, Any]) -> tuple[str | None, str | None]:
    return item.get("entity_type"), item.get("entity_key")


def relation_key(item: dict[str, Any]) -> tuple[Any, ...]:
    subject = item.get("subject") or {}
    obj = item.get("object") or {}
    return (
        subject.get("entity_type"),
        subject.get("entity_key"),
        item.get("predicate"),
        obj.get("entity_type"),
        obj.get("entity_key"),
    )


def required_relation_key(item: dict[str, Any]) -> tuple[Any, ...]:
    subject = item["subject"]
    obj = item["object"]
    return (
        subject["entity_type"],
        subject["entity_key"],
        item["predicate"],
        obj["entity_type"],
        obj["entity_key"],
    )


def claim_matches(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    if actual.get("subject") != expected.get("subject"):
        return False
    if actual.get("predicate") != expected.get("predicate"):
        return False
    if actual.get("value") != expected.get("value"):
        return False
    if "unit" in expected and actual.get("unit") != expected.get("unit"):
        return False
    return True


def event_matches(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    for key in ("event_type", "event_key", "classification", "occurred_on"):
        if key in expected and actual.get(key) != expected.get(key):
            return False
    return True


def evaluate_discovery(
    response: dict[str, Any] | None,
    parse_error: str | None,
    case: dict[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    checks.append(
        check(
            "discovery_json",
            response is not None,
            "discovery response is valid JSON" if response is not None else (parse_error or "invalid JSON"),
            weight=5,
            critical=True,
        )
    )
    if response is None:
        for check_id, weight, critical in [
            ("required_files", 10, False),
            ("canonical_write_boundary", 5, True),
            ("database_write_boundary", 5, True),
            ("pack_validation_awareness", 5, False),
            ("undeclared_capability_boundary", 5, True),
        ]:
            checks.append(check(check_id, False, "unavailable because discovery JSON could not be parsed", weight=weight, critical=critical))
        return checks

    required_files = {normalize_path(v) for v in case["discovery"]["required_files"]}
    next_files = {normalize_path(v) for v in response.get("next_files", []) if isinstance(v, str)}
    missing_files = sorted(required_files - next_files)
    checks.append(
        check(
            "required_files",
            not missing_files,
            "all required repository contracts discovered" if not missing_files else f"missing: {', '.join(missing_files)}",
            weight=10,
        )
    )

    expected = case["discovery"]["expected"]
    checks.append(
        check(
            "canonical_write_boundary",
            response.get("can_write_canonical") is expected["can_write_canonical"],
            f"can_write_canonical={response.get('can_write_canonical')!r}",
            weight=5,
            critical=True,
        )
    )
    checks.append(
        check(
            "database_write_boundary",
            response.get("can_write_database_directly") is expected["can_write_database_directly"],
            f"can_write_database_directly={response.get('can_write_database_directly')!r}",
            weight=5,
            critical=True,
        )
    )
    checks.append(
        check(
            "pack_validation_awareness",
            response.get("must_validate_pack_before_proposing") is expected["must_validate_pack_before_proposing"],
            f"must_validate_pack_before_proposing={response.get('must_validate_pack_before_proposing')!r}",
            weight=5,
        )
    )
    checks.append(
        check(
            "undeclared_capability_boundary",
            response.get("assume_undeclared_capabilities") is expected["assume_undeclared_capabilities"],
            f"assume_undeclared_capabilities={response.get('assume_undeclared_capabilities')!r}",
            weight=5,
            critical=True,
        )
    )
    return checks


def evaluate_contribution(
    packet: dict[str, Any] | None,
    parse_error: str | None,
    case: dict[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    checks.append(
        check(
            "contribution_json",
            packet is not None,
            "contribution response is valid JSON" if packet is not None else (parse_error or "invalid JSON"),
            weight=5,
            critical=True,
        )
    )
    if packet is None:
        for check_id, weight, critical in [
            ("protocol_valid", 15, True),
            ("no_existing_entity_redeclaration", 10, True),
            ("required_new_entities", 5, False),
            ("all_factual_statuses_proposed", 10, True),
            ("required_claims", 10, False),
            ("required_event", 10, True),
            ("no_completed_future_events", 10, True),
            ("no_unsupported_relation_inference", 10, True),
            ("source_diversity", 5, False),
            ("event_corroboration", 5, False),
        ]:
            checks.append(check(check_id, False, "unavailable because contribution JSON could not be parsed", weight=weight, critical=critical))
        return checks

    protocol_ok, protocol_detail = protocol_validation(packet)
    checks.append(check("protocol_valid", protocol_ok, protocol_detail, weight=15, critical=True))

    declared_entities = {entity_ref(item) for item in packet.get("entities", [])}
    existing_entities = {
        (item["entity_type"], item["entity_key"])
        for item in case["canonical_lookup"]["existing_entities"]
    }
    redeclared = sorted(existing_entities & declared_entities)
    checks.append(
        check(
            "no_existing_entity_redeclaration",
            not redeclared,
            "existing canonical identities are referenced, not redeclared"
            if not redeclared
            else f"redeclared canonical entities: {redeclared}",
            weight=10,
            critical=True,
        )
    )

    required_new = {
        (item["entity_type"], item["entity_key"])
        for item in case["expected"]["new_entities"]
    }
    missing_new = sorted(required_new - declared_entities)
    checks.append(
        check(
            "required_new_entities",
            not missing_new,
            "all expected new identities declared" if not missing_new else f"missing new identities: {missing_new}",
            weight=5,
        )
    )

    facts = list(packet.get("claims", [])) + list(packet.get("relations", [])) + list(packet.get("events", []))
    bad_status = [item.get("id", "<missing-id>") for item in facts if item.get("status") != "proposed"]
    checks.append(
        check(
            "all_factual_statuses_proposed",
            not bad_status,
            "all incoming factual objects remain proposed" if not bad_status else f"non-proposed facts: {bad_status}",
            weight=10,
            critical=True,
        )
    )

    missing_claims = []
    actual_claims = list(packet.get("claims", []))
    for expected_claim in case["expected"]["required_claims"]:
        if not any(claim_matches(actual, expected_claim) for actual in actual_claims):
            missing_claims.append(expected_claim)
    checks.append(
        check(
            "required_claims",
            not missing_claims,
            "all directly supported pack-legal claims preserved"
            if not missing_claims
            else "missing supported claims: " + ", ".join(item["predicate"] for item in missing_claims),
            weight=10,
        )
    )

    actual_events = list(packet.get("events", []))
    missing_events = []
    for expected_event in case["expected"]["required_events"]:
        if not any(event_matches(actual, expected_event) for actual in actual_events):
            missing_events.append(expected_event["event_key"])
    checks.append(
        check(
            "required_event",
            not missing_events,
            "required product_release Event modeled correctly" if not missing_events else f"missing/mismatched event(s): {missing_events}",
            weight=10,
            critical=True,
        )
    )

    forbidden_event_types = set(case["expected"]["forbidden_event_types"])
    forbidden_events = [
        item.get("id", item.get("event_key", "<event>"))
        for item in actual_events
        if item.get("event_type") in forbidden_event_types
    ]
    checks.append(
        check(
            "no_completed_future_events",
            not forbidden_events,
            "future shipping plan was not converted into completed deployment/mass production"
            if not forbidden_events
            else f"forbidden completed-event inference: {forbidden_events}",
            weight=10,
            critical=True,
        )
    )

    forbidden_relation_keys = {required_relation_key(item) for item in case["expected"]["forbidden_relations"]}
    actual_relation_keys = {relation_key(item) for item in packet.get("relations", [])}
    inferred_relations = sorted(forbidden_relation_keys & actual_relation_keys)
    checks.append(
        check(
            "no_unsupported_relation_inference",
            not inferred_relations,
            "no manufactures relation inferred from release wording"
            if not inferred_relations
            else f"unsupported relation inference: {inferred_relations}",
            weight=10,
            critical=True,
        )
    )

    source_urls = {
        evidence.get("source", {}).get("url")
        for evidence in packet.get("evidence", [])
        if evidence.get("source", {}).get("url")
    }
    min_sources = int(case["expected"]["min_distinct_source_urls"])
    checks.append(
        check(
            "source_diversity",
            len(source_urls) >= min_sources,
            f"distinct evidence sources={len(source_urls)}, required>={min_sources}",
            weight=5,
        )
    )

    evidence_by_id = {item.get("id"): item for item in packet.get("evidence", [])}
    required_event_keys = {item["event_key"] for item in case["expected"]["required_events"]}
    min_event_evidence = int(case["expected"]["event_min_evidence"])
    event_evidence_failures = []
    for event in actual_events:
        if event.get("event_key") not in required_event_keys:
            continue
        linked = [evidence_by_id.get(eid) for eid in event.get("evidence_ids", [])]
        linked_urls = {
            item.get("source", {}).get("url")
            for item in linked
            if isinstance(item, dict) and item.get("source", {}).get("url")
        }
        if len(linked) < min_event_evidence or len(linked_urls) < min_event_evidence:
            event_evidence_failures.append(
                f"{event.get('event_key')}: evidence={len(linked)}, distinct_sources={len(linked_urls)}"
            )
    checks.append(
        check(
            "event_corroboration",
            not event_evidence_failures,
            "required Event is corroborated by distinct sources"
            if not event_evidence_failures
            else "; ".join(event_evidence_failures),
            weight=5,
        )
    )
    return checks


def build_report(
    case: dict[str, Any],
    discovery: dict[str, Any] | None,
    discovery_error: str | None,
    contribution: dict[str, Any] | None,
    contribution_error: str | None,
    *,
    min_score: float,
    command: str | None,
) -> dict[str, Any]:
    checks = evaluate_discovery(discovery, discovery_error, case)
    checks.extend(evaluate_contribution(contribution, contribution_error, case))
    total_weight = sum(item["weight"] for item in checks)
    earned_weight = sum(item["weight"] for item in checks if item["passed"])
    score = round((earned_weight / total_weight) * 100, 1) if total_weight else 0.0
    critical_failures = [item["id"] for item in checks if item["critical"] and not item["passed"]]
    passed = score >= min_score and not critical_failures
    return {
        "benchmark_version": case["benchmark_version"],
        "case_id": case["id"],
        "model_command": command,
        "score": score,
        "min_score": min_score,
        "passed": passed,
        "critical_failures": critical_failures,
        "checks": checks,
    }


def build_discovery_prompt(case: dict[str, Any]) -> str:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    return f"""You are an external AI with zero prior knowledge of AIMAN or this repository.
You are doing a cold-start interoperability benchmark.

You currently have access ONLY to the repository README below.
Do not invent files, permissions, APIs, or capabilities.

Return JSON only with exactly this shape:
{{
  "next_files": ["path", "..."],
  "can_write_canonical": false,
  "can_write_database_directly": false,
  "must_validate_pack_before_proposing": true,
  "assume_undeclared_capabilities": false
}}

The next_files list should contain the repository contracts you need to read before safely proposing a robotics world change.

===== README.md =====
{readme}
"""


def stage_two_case_payload(case: dict[str, Any]) -> dict[str, Any]:
    return {
        key: case[key]
        for key in (
            "benchmark_version",
            "id",
            "title",
            "description",
            "pack",
            "created_at",
            "contributor",
            "canonical_lookup",
            "evidence_fixture",
            "task_rules",
        )
    }


def build_contribution_prompt(case: dict[str, Any]) -> str:
    chunks = [
        "You are the same external AI, still with zero private AIMAN context.",
        "Use only the public repository contracts below and the benchmark task fixture.",
        "Return exactly one World Model Contribution Protocol v0.3 JSON object. No Markdown or commentary.",
        "Do not claim that the proposal is canonical or verified.",
        "",
    ]
    for relative in case["context_files"]:
        path = ROOT / relative
        chunks.append(f"===== {relative} =====")
        chunks.append(path.read_text(encoding="utf-8"))
        chunks.append("")
    chunks.append("===== BENCHMARK TASK FIXTURE =====")
    chunks.append(json.dumps(stage_two_case_payload(case), ensure_ascii=False, indent=2))
    chunks.append("")
    chunks.append("Produce the safest complete contribution supported by the fixture and current pack.")
    return "\n".join(chunks)


def run_model_command(command: str, prompt: str, *, timeout: int) -> tuple[str, str, int]:
    proc = subprocess.run(
        command,
        shell=True,
        input=prompt,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        cwd=ROOT,
        env=os.environ.copy(),
    )
    return proc.stdout, proc.stderr, proc.returncode


def response_from_path(path: Path) -> tuple[dict[str, Any] | None, str | None, str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        return extract_json_object(raw), None, raw
    except BenchmarkError as exc:
        return None, str(exc), raw


def print_report(report: dict[str, Any]) -> None:
    status = "PASS" if report["passed"] else "FAIL"
    print(f"{status} cold-start benchmark {report['case_id']}: score={report['score']} min={report['min_score']}")
    for item in report["checks"]:
        marker = "PASS" if item["passed"] else "FAIL"
        critical = " critical" if item["critical"] else ""
        print(f"[{marker}]{critical} {item['id']}: {item['detail']}")
    if report["critical_failures"]:
        print("critical_failures=" + ",".join(report["critical_failures"]))


def run_self_test() -> int:
    case = load_json(DEFAULT_CASE)
    discovery = load_json(REFERENCE_DISCOVERY)
    contribution = load_json(REFERENCE_CONTRIBUTION)

    reference = build_report(
        case,
        discovery,
        None,
        contribution,
        None,
        min_score=100.0,
        command="reference-fixture",
    )
    if not reference["passed"] or reference["score"] != 100.0:
        print_report(reference)
        raise BenchmarkError("reference fixture must score 100")

    duplicate = copy.deepcopy(contribution)
    duplicate["entities"].append(
        {
            "id": "entity:company-aster-robotics",
            "entity_type": "company",
            "entity_key": "aster-robotics",
            "name": "Aster Robotics",
        }
    )
    duplicate_report = build_report(case, discovery, None, duplicate, None, min_score=0, command="self-test")
    duplicate_check = next(item for item in duplicate_report["checks"] if item["id"] == "no_existing_entity_redeclaration")
    if duplicate_check["passed"]:
        raise BenchmarkError("duplicate canonical identity self-test was not detected")

    overreach = copy.deepcopy(contribution)
    overreach["relations"].append(
        {
            "id": "relation:aster-robotics-manufactures-aster-r1",
            "subject": {"entity_type": "company", "entity_key": "aster-robotics"},
            "predicate": "manufactures",
            "object": {"entity_type": "robot", "entity_key": "aster-r1"},
            "status": "proposed",
            "observed_at": case["created_at"],
            "evidence_ids": ["evidence:aster-r1-manufactures-overreach"],
        }
    )
    overreach["evidence"].append(
        {
            "id": "evidence:aster-r1-manufactures-overreach",
            "target": {"kind": "relation", "id": "relation:aster-robotics-manufactures-aster-r1"},
            "source": {
                "url": "https://example.invalid/aster/r1",
                "title": "Aster R1 official product page",
                "publisher": "Aster Robotics",
                "source_type": "first_party",
            },
            "locator": "release wording only",
            "excerpt": "Aster Robotics today released Aster R1.",
            "captured_at": "2026-09-21T14:00:00Z",
            "stance": "supports",
        }
    )
    overreach_report = build_report(case, discovery, None, overreach, None, min_score=0, command="self-test")
    overreach_check = next(item for item in overreach_report["checks"] if item["id"] == "no_unsupported_relation_inference")
    if overreach_check["passed"]:
        raise BenchmarkError("unsupported relation self-test was not detected")

    future = copy.deepcopy(contribution)
    future["events"][0]["event_type"] = "deployment"
    future_report = build_report(case, discovery, None, future, None, min_score=0, command="self-test")
    future_check = next(item for item in future_report["checks"] if item["id"] == "no_completed_future_events")
    if future_check["passed"]:
        raise BenchmarkError("future-plan-as-completed-event self-test was not detected")

    escalated = copy.deepcopy(contribution)
    escalated["claims"][0]["status"] = "verified"
    escalated_report = build_report(case, discovery, None, escalated, None, min_score=0, command="self-test")
    protocol_check = next(item for item in escalated_report["checks"] if item["id"] == "protocol_valid")
    status_check = next(item for item in escalated_report["checks"] if item["id"] == "all_factual_statuses_proposed")
    if protocol_check["passed"] or status_check["passed"]:
        raise BenchmarkError("self-promoted status self-test was not detected")

    print("cold-start benchmark self-test: ok")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or score the AIMAN World Model Cold Start Benchmark")
    parser.add_argument("--case", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--command", help="model command that reads the prompt from stdin and writes its answer to stdout")
    parser.add_argument("--discovery-response", type=Path)
    parser.add_argument("--contribution-response", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--min-score", type=float, default=85.0)
    parser.add_argument("--report-only", action="store_true", help="always exit 0 after producing the report")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    case = load_json(args.case)
    output_dir = args.output_dir or Path(os.environ.get("TMPDIR", "/tmp")) / "iwm-cold-start" / case["id"]
    output_dir.mkdir(parents=True, exist_ok=True)

    discovery_prompt = build_discovery_prompt(case)
    contribution_prompt = build_contribution_prompt(case)
    (output_dir / "discovery.prompt.txt").write_text(discovery_prompt, encoding="utf-8")
    (output_dir / "contribution.prompt.txt").write_text(contribution_prompt, encoding="utf-8")

    if args.command:
        discovery_raw, discovery_stderr, discovery_rc = run_model_command(args.command, discovery_prompt, timeout=args.timeout)
        contribution_raw, contribution_stderr, contribution_rc = run_model_command(args.command, contribution_prompt, timeout=args.timeout)
        (output_dir / "discovery.raw.txt").write_text(discovery_raw, encoding="utf-8")
        (output_dir / "discovery.stderr.txt").write_text(discovery_stderr, encoding="utf-8")
        (output_dir / "contribution.raw.txt").write_text(contribution_raw, encoding="utf-8")
        (output_dir / "contribution.stderr.txt").write_text(contribution_stderr, encoding="utf-8")
        if discovery_rc != 0:
            discovery_raw += f"\nmodel command exit code: {discovery_rc}\n"
        if contribution_rc != 0:
            contribution_raw += f"\nmodel command exit code: {contribution_rc}\n"
        try:
            discovery = extract_json_object(discovery_raw)
            discovery_error = None
        except BenchmarkError as exc:
            discovery = None
            discovery_error = str(exc)
        try:
            contribution = extract_json_object(contribution_raw)
            contribution_error = None
        except BenchmarkError as exc:
            contribution = None
            contribution_error = str(exc)
    else:
        if not args.discovery_response or not args.contribution_response:
            parser.error("provide --command or both --discovery-response and --contribution-response")
        discovery, discovery_error, discovery_raw = response_from_path(args.discovery_response)
        contribution, contribution_error, contribution_raw = response_from_path(args.contribution_response)
        (output_dir / "discovery.raw.txt").write_text(discovery_raw, encoding="utf-8")
        (output_dir / "contribution.raw.txt").write_text(contribution_raw, encoding="utf-8")

    if discovery is not None:
        (output_dir / "discovery.json").write_text(json.dumps(discovery, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if contribution is not None:
        (output_dir / "contribution.json").write_text(json.dumps(contribution, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = build_report(
        case,
        discovery,
        discovery_error,
        contribution,
        contribution_error,
        min_score=args.min_score,
        command=args.command,
    )
    (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print_report(report)
    print(f"artifacts={output_dir}")

    if args.report_only:
        return 0
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BenchmarkError as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        raise SystemExit(2)
