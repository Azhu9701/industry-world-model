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
```

This test checks the fixture's deterministic inputs and expected outputs;
it **does not assert that review/materialization, change outbox, content
references, channel updates or recovery already exist**. Those remain WS-02
and WS-03 deliverables, with separate runtime tests and receipts.

The test must never write to canonical PostgreSQL, publish content, use real
API keys, or treat a synthetic claim as a public truth.
