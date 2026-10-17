# World Studio WS-01 — isolated synthetic fixture

This directory contains **fictional demonstration data only**. It is not a
`contributions/` packet, a verified industry fact, an authorized external
customer workspace, or a persisted World Snapshot.

`payload-revision.json` describes Demo Robot A's payload correction from
**5 kg → 4 kg**, preserving both versions and distinct evidence IDs. Six
registered content versions are fixed: four refer to the old claim in the
same `world` and `pack`, two must remain unaffected. A draft's existing
approval becomes invalid and three published items enter a **correction
review queue**, not an automatic publication command.

Run locally:

```sh
python3 scripts/test-world-studio-fixture.py
python3 scripts/test-world-studio-impact.py
python3 scripts/world_studio_impact.py tests/fixtures/world-studio/payload-revision.json
```

This test checks the fixture's deterministic inputs and expected outputs;
it **does not assert that review/materialization, change outbox, persisted
content references, channel updates or recovery already exist**. The pure
`world_studio_impact.py` prototype computes draft-review and published-correction
task *suggestions* from this fixture only. It rejects non-synthetic input,
is deterministic under repeated and reordered calls, and never publishes,
updates approvals, touches a database, or reads private customer material. Those remain WS-02
and WS-03 deliverables, with separate runtime tests and receipts.

The test must never write to canonical PostgreSQL, publish content, use real
API keys, or treat a synthetic claim as a public truth.
