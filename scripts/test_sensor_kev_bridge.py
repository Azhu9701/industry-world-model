#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "scripts" / "sensor_kev_to_contribution.py"
PUBLISHER_PATH = ROOT / "scripts" / "publish_sensor_kev_pr.py"
FIXTURE = ROOT / "examples" / "robotics" / "sensor-kev-viabot-series-a.json"
SCHEMA = ROOT / "protocol" / "adapters" / "sensor-kev-event.schema.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = load_module("sensor_kev_adapter_test", ADAPTER_PATH)
publisher = load_module("sensor_kev_publisher_test", PUBLISHER_PATH)


def main() -> int:
    schema = json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(schema)

    envelope = json.loads(FIXTURE.read_text())
    adapter.validate_envelope(envelope)
    ok, reasons, mapped = adapter.eligibility(envelope)
    assert ok is True
    assert reasons == []
    assert mapped == "funding"

    contribution = adapter.convert(envelope)
    assert contribution["protocol_version"] == "0.3.0"
    assert contribution["events"][0]["event_type"] == "funding"
    assert contribution["events"][0]["status"] == "proposed"
    assert len(contribution["evidence"]) == 2
    assert contribution["metadata"]["automation"]["canonical_write"] is False
    assert contribution["metadata"]["automation"]["auto_merge"] is False
    assert publisher.branch_name(envelope).startswith("auto-contrib/")
    assert publisher.pr_title(envelope).startswith("contrib(robotics):")

    needs_second = copy.deepcopy(envelope)
    needs_second["kev"]["decision_packet"]["needs_second_source"] = True
    ok, reasons, _ = adapter.eligibility(needs_second)
    assert not ok and "needs_second_source" in reasons

    one_source = copy.deepcopy(envelope)
    one_source["sensor"]["sources"] = one_source["sensor"]["sources"][:1]
    first_url = one_source["sensor"]["sources"][0]["url"]
    for fact in one_source["sensor"]["facts"]:
        fact["source_urls"] = [first_url]
    ok, reasons, _ = adapter.eligibility(one_source)
    assert not ok and "fewer_than_two_sources" in reasons

    product = copy.deepcopy(envelope)
    product["kev"]["decision_packet"]["event_type"] = "product"
    product["kev"]["decision_packet"]["commercialization_stage"] = "launch"
    ok, reasons, mapped = adapter.eligibility(product)
    assert ok and reasons == [] and mapped == "product_release"

    policy = copy.deepcopy(envelope)
    policy["kev"]["decision_packet"]["event_type"] = "policy"
    ok, reasons, mapped = adapter.eligibility(policy)
    assert not ok and mapped is None
    assert "ontology_event_mapping_requires_review" in reasons

    print("ok Sensor -> Kev -> Contribution auto-PR bridge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
