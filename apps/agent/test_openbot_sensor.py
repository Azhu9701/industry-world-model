import unittest

from openbot_sensor import build_plan, normalize_batch, normalize_record, resolve_identity


def record(**overrides):
    value = {
        "record_type": "dataset",
        "record_id": "demo-dataset",
        "record_url": "https://openbot.ai/datasets/demo-dataset",
        "name": "Demo Dataset",
        "aliases": ["Demo-DS"],
        "upstream_sources": [
            {
                "url": "https://github.com/example/demo-dataset",
                "title": "Demo Dataset repository",
                "publisher": "Example Robotics",
                "source_type": "repository",
                "supports": {
                    "release_date": "2026-01-05",
                    "license": "Apache-2.0"
                },
            }
        ],
        "hints": {
            "release_date": "2026-01-05",
            "license": "Apache-2.0",
            "repository": "https://github.com/example/demo-dataset",
        },
        "external_assessment": {
            "provider": "openbot",
            "selection_readiness": 73,
            "confidence": 0.48,
        },
    }
    value.update(overrides)
    return value


class NormalizeRecordTest(unittest.TestCase):
    def test_openbot_is_discovery_not_canonical(self) -> None:
        candidate = normalize_record(record())
        self.assertEqual(candidate["provider"], "openbot")
        self.assertEqual(candidate["status"], "candidate")
        self.assertFalse(candidate["canonical"])
        self.assertEqual(candidate["record_type"], "dataset")

    def test_duplicate_batch_collapses_identical_provider_record(self) -> None:
        result = normalize_batch([record(), record()])
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(len(result["duplicates"]), 1)
        self.assertEqual(result["conflicts"], [])

    def test_same_provider_key_with_changed_content_is_conflict(self) -> None:
        changed = record(hints={"license": "MIT"})
        result = normalize_batch([record(), changed])
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(len(result["conflicts"]), 1)

    def test_unsupported_hint_is_preserved_but_separated(self) -> None:
        candidate = normalize_record(record(hints={"license": "MIT", "robot_count": 500}))
        self.assertEqual(candidate["hints"], {"license": "MIT"})
        self.assertEqual(candidate["unsupported_hints"], {"robot_count": 500})


class IdentityResolutionTest(unittest.TestCase):
    def test_existing_entity_resolves_by_exact_normalized_name(self) -> None:
        candidate = normalize_record(record())
        result = resolve_identity(
            candidate,
            [
                {
                    "entityType": "dataset",
                    "entityKey": "demo-dataset",
                    "name": "Demo Dataset",
                    "attributes": {},
                }
            ],
        )
        self.assertEqual(result["status"], "existing")

    def test_new_entity_when_no_exact_match_exists(self) -> None:
        candidate = normalize_record(record())
        result = resolve_identity(candidate, [])
        self.assertEqual(result["status"], "new")

    def test_multiple_exact_matches_require_review(self) -> None:
        candidate = normalize_record(record())
        result = resolve_identity(
            candidate,
            [
                {
                    "entityType": "dataset",
                    "entityKey": "demo-a",
                    "name": "Demo Dataset",
                    "attributes": {},
                },
                {
                    "entityType": "dataset",
                    "entityKey": "demo-b",
                    "name": "Other Name",
                    "attributes": {"aliases": ["Demo Dataset"]},
                },
            ],
        )
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(len(result["matches"]), 2)


class ProposalPlanningTest(unittest.TestCase):
    def test_existing_entity_emits_claims_not_entity(self) -> None:
        candidate = normalize_record(record())
        plan = build_plan(
            candidate,
            [
                {
                    "entityType": "dataset",
                    "entityKey": "demo-dataset",
                    "name": "Demo Dataset",
                    "attributes": {},
                }
            ],
        )
        kinds = [proposal["kind"] for proposal in plan["proposals"]]
        self.assertNotIn("entity", kinds)
        self.assertEqual(kinds.count("claim"), 3)
        self.assertTrue(
            all(
                proposal.get("source", {}).get("url", "").startswith(
                    "https://github.com/example/"
                )
                for proposal in plan["proposals"]
            )
        )

    def test_new_entity_emits_entity_plus_evidence_backed_claims(self) -> None:
        candidate = normalize_record(record(record_type="model", name="Demo Model"))
        plan = build_plan(candidate, [])
        kinds = [proposal["kind"] for proposal in plan["proposals"]]
        self.assertEqual(kinds[0], "entity")
        self.assertIn("claim", kinds)

    def test_identity_conflict_blocks_all_proposals(self) -> None:
        candidate = normalize_record(record())
        plan = build_plan(
            candidate,
            [
                {
                    "entityType": "dataset",
                    "entityKey": "a",
                    "name": "Demo Dataset",
                    "attributes": {},
                },
                {
                    "entityType": "dataset",
                    "entityKey": "b",
                    "name": "Demo-DS",
                    "attributes": {},
                },
            ],
        )
        self.assertEqual(plan["resolution"]["status"], "review_required")
        self.assertEqual(plan["proposals"], [])
        self.assertEqual(plan["gaps"][0]["kind"], "identity_conflict")

    def test_missing_upstream_does_not_promote_openbot_hint(self) -> None:
        candidate = normalize_record(
            record(
                upstream_sources=[
                    {
                        "url": "https://openbot.ai/datasets/demo-dataset",
                        "title": "OpenBot record",
                        "source_type": "other",
                    }
                ]
            )
        )
        plan = build_plan(candidate, [])
        claims = [proposal for proposal in plan["proposals"] if proposal["kind"] == "claim"]
        self.assertEqual(claims, [])
        self.assertTrue(
            all(gap["kind"] == "missing_upstream_evidence" for gap in plan["gaps"])
        )

    def test_upstream_presence_without_field_support_does_not_promote_hint(self) -> None:
        candidate = normalize_record(
            record(
                upstream_sources=[
                    {
                        "url": "https://example.com/demo",
                        "title": "Official demo page",
                        "source_type": "official",
                    }
                ],
                hints={"release_date": "2026-01-05"},
            )
        )
        plan = build_plan(candidate, [])
        claims = [proposal for proposal in plan["proposals"] if proposal["kind"] == "claim"]
        self.assertEqual(claims, [])
        self.assertEqual(plan["gaps"][0]["kind"], "missing_upstream_evidence")

    def test_external_assessment_is_not_promoted_to_claim(self) -> None:
        candidate = normalize_record(record())
        plan = build_plan(candidate, [])
        predicates = {
            proposal["payload"].get("predicate")
            for proposal in plan["proposals"]
            if proposal["kind"] == "claim"
        }
        self.assertNotIn("selection_readiness", predicates)
        self.assertEqual(plan["external_assessment"]["provider"], "openbot")

    def test_unsupported_hint_stays_gap(self) -> None:
        candidate = normalize_record(record(hints={"license": "MIT", "robot_count": 500}))
        plan = build_plan(candidate, [])
        predicates = {
            proposal["payload"].get("predicate")
            for proposal in plan["proposals"]
            if proposal["kind"] == "claim"
        }
        self.assertEqual(predicates, set())
        gap_kinds = {gap["kind"] for gap in plan["gaps"]}
        self.assertEqual(gap_kinds, {"missing_upstream_evidence", "unsupported_hint"})


if __name__ == "__main__":
    unittest.main()
