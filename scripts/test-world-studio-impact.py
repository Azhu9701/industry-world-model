#!/usr/bin/env python3
"""Pure WS-01 impact behavior tests; no model, network, DB or publishing."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from world_studio_impact import FixtureValidationError, impact_plan

FIXTURE = ROOT / "tests/fixtures/world-studio/payload-revision.json"


class WorldStudioWS01ImpactTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_exact_4_of_6_impact_and_distinct_actions(self):
        plan = impact_plan(self.data)
        expected = self.data["expected"]
        self.assertEqual(set(plan["affectedContentIds"]), set(expected["affectedContentIds"]))
        self.assertEqual(set(plan["unaffectedContentIds"]), set(expected["unaffectedContentIds"]))
        self.assertEqual(len(plan["tasks"]), 4)
        self.assertEqual(
            {t["contentId"] for t in plan["tasks"] if t["approvalInvalidated"]},
            set(expected["draftApprovalsInvalidated"]),
        )
        self.assertEqual(
            {t["contentId"] for t in plan["tasks"] if t["action"] == "review_published_correction"},
            set(expected["publishedCorrectionQueue"]),
        )
        self.assertTrue(all(t["status"] == "needs_editorial_review" for t in plan["tasks"]))
        self.assertTrue(all(not t["draftCreated"] and not t["published"] for t in plan["tasks"]))
        self.assertEqual(plan["unregisteredContentCoverage"], "unknown")
        self.assertFalse(plan["persisted"])

    def test_order_and_repeated_replay_are_deterministic(self):
        one = impact_plan(self.data)
        duplicate = impact_plan(copy.deepcopy(self.data))
        reordered = copy.deepcopy(self.data)
        reordered["contents"].reverse()
        self.assertEqual(one, duplicate)
        self.assertEqual(one, impact_plan(reordered))
        self.assertEqual(len({t["taskKey"] for t in one["tasks"]}), 4)
        self.assertTrue(all(":revision-" in t["taskKey"] for t in one["tasks"]))

    def test_bare_id_wrong_pack_world_or_revision_does_not_match(self):
        for field, wrong in (("world", "world:manufacturing-demo"),
                             ("pack", "manufacturing"),
                             ("claimId", "claim:demo-other-field"),
                             ("version", 99)):
            with self.subTest(field=field):
                other = copy.deepcopy(self.data)
                for record in other["contents"]:
                    for ref in record["factReferences"]:
                        if (ref.get("world") == other["world"]
                                and ref.get("claimId") == other["change"]["oldClaim"]["id"]):
                            ref[field] = wrong
                result = impact_plan(other)
                self.assertEqual(result["affectedContentIds"], [])

    def test_missing_approval_is_not_invented(self):
        other = copy.deepcopy(self.data)
        draft = next(c for c in other["contents"] if c["state"] == "draft")
        draft["approvedRevision"] = None
        record = next(t for t in impact_plan(other)["tasks"] if t["contentId"] == draft["id"])
        self.assertEqual(record["action"], "re_review_draft")
        self.assertFalse(record["approvalInvalidated"])

    def test_invalid_content_or_unverified_change_fails_closed(self):
        for mutate in (
            lambda d: d.update(synthetic=False),
            lambda d: d["change"]["newClaim"].update(status="proposed"),
            lambda d: d["change"]["oldClaim"].update(evidenceIds=[]),
            lambda d: d["contents"].append(copy.deepcopy(d["contents"][0])),
            lambda d: d["contents"][0].update(state="unknown"),
            lambda d: d["contents"][0].update(revision=True),
        ):
            other = copy.deepcopy(self.data)
            mutate(other)
            with self.subTest(mutate=mutate):
                with self.assertRaises(FixtureValidationError):
                    impact_plan(other)


if __name__ == "__main__":
    unittest.main()
