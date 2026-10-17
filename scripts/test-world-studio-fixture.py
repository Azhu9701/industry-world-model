#!/usr/bin/env python3
"""WS-01 fixture contract: deterministic inputs/expectations, NOT Studio runtime."""
import json
import unittest
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "tests/fixtures/world-studio/payload-revision.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def references_old_claim(content, world, pack, old):
    return any(
        ref.get("world") == world
        and ref.get("pack") == pack
        and ref.get("claimId") == old["id"]
        and ref.get("version") == old["version"]
        for ref in content.get("factReferences", [])
    )


class WorldStudioWS01FixtureTest(unittest.TestCase):
    def setUp(self):
        self.data = load_fixture()

    def test_synthetic_fixture_remains_separate_from_public_contributions(self):
        self.assertTrue(self.data["synthetic"])
        self.assertIn("NOT a real-world claim", self.data["fixturePurpose"])
        self.assertEqual(self.data["pack"], "robotics")
        self.assertNotIn("contributions", FIXTURE.parts)
        self.assertEqual(self.data["entity"]["entityType"], "robot")

    def test_revision_preserves_identity_evidence_and_history(self):
        change = self.data["change"]
        old, new = change["oldClaim"], change["newClaim"]
        self.assertEqual((old["predicate"], new["predicate"]), ("payload", "payload"))
        self.assertEqual((old["value"], new["value"]), (5, 4))
        self.assertEqual((old["unit"], new["unit"]), ("kg", "kg"))
        self.assertEqual((old["status"], new["status"]), ("superseded", "verified"))
        self.assertEqual(new["supersedes"], [old["id"]])
        self.assertEqual(new["version"], old["version"] + 1)
        self.assertTrue(old["evidenceIds"] and new["evidenceIds"])
        self.assertNotEqual(old["evidenceIds"], new["evidenceIds"])
        self.assertTrue(self.data["expected"]["oldClaimRetained"])
        self.assertTrue(self.data["expected"]["newClaimSupersedesOld"])

    def test_impact_set_exactly_four_of_six(self):
        data = self.data
        contents = data["contents"]
        ids = [item["id"] for item in contents]
        self.assertEqual(len(ids), 6)
        self.assertEqual(len(ids), len(set(ids)))
        old = data["change"]["oldClaim"]
        impacted = {
            item["id"] for item in contents
            if references_old_claim(item, data["world"], data["pack"], old)
        }
        unaffected = set(ids) - impacted
        self.assertEqual(impacted, set(data["expected"]["affectedContentIds"]))
        self.assertEqual(unaffected, set(data["expected"]["unaffectedContentIds"]))
        self.assertEqual(len(impacted), 4)
        self.assertEqual(len(unaffected), 2)
        self.assertNotIn("content:other-world-same-claim-id", impacted)

    def test_approval_invalidation_and_published_correction_are_distinct(self):
        data = self.data
        by_id = {item["id"]: item for item in data["contents"]}
        affected = set(data["expected"]["affectedContentIds"])
        expired = set(data["expected"]["draftApprovalsInvalidated"])
        corrections = set(data["expected"]["publishedCorrectionQueue"])
        self.assertTrue(expired <= affected)
        self.assertTrue(corrections <= affected)
        self.assertTrue(expired.isdisjoint(corrections))
        self.assertTrue(all(by_id[i]["state"] == "draft" for i in expired))
        self.assertTrue(all(by_id[i]["approvedRevision"] == by_id[i]["revision"] for i in expired))
        self.assertTrue(all(by_id[i]["state"] == "published" for i in corrections))
        self.assertEqual(expired | corrections, affected)
        self.assertEqual(data["expected"]["unregisteredContentCoverage"], "unknown")
        self.assertTrue(data["expected"]["noAutomaticPublications"])


if __name__ == "__main__":
    unittest.main()
