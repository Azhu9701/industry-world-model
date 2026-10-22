# OpenBot Sensor Integration v0

Status: first-stage adapter

OpenBot is integrated as an upstream discovery sensor for robotics datasets and models. It is intentionally **not** treated as a mirrored database or canonical source.

## Why a sensor, not an importer

The World Model already has a review-first intake path:

```text
discover -> extract -> resolve -> evidence -> propose -> validate -> review
```

OpenBot fits at `discover`. Its records can reveal candidate datasets/models and useful upstream URLs, but AIMAN still resolves identity and returns to primary sources before proposing facts.

This keeps the canonical model independent of OpenBot's schema, scoring model, availability, or future API changes.

## v0 data flow

```text
OpenBot record
    |
    v
aiman.openbot_candidate.v0
    |
    +-- provider = openbot
    +-- canonical = false
    +-- original record id/url
    +-- name + aliases
    +-- upstream source candidates
    +-- supported factual hints
    +-- unsupported hints
    +-- external assessment
    +-- deterministic candidate fingerprint
    |
    v
exact identity resolution
    |
    +-- existing -> enrichment
    +-- new -> entity proposal
    +-- multiple matches -> review_required
    |
    v
primary-source gate
    |
    +-- upstream source explicitly supports exact value -> proposed Claim
    +-- only OpenBot source -> knowledge gap
    |
    v
POST /api/v1/proposals
    |
    v
ingest_jobs + review_tasks
```

No path bypasses the existing review boundary.

## Supported scope

v0 accepts only the existing robotics entity types:

- `dataset`
- `model`

It emits factual Claim proposals only for predicates already present in the robotics pack:

- `release_date`
- `license`
- `repository`

Other OpenBot fields are preserved as unsupported hints or external assessment context. They are not silently discarded and are not promoted to canonical facts.

## Identity policy

Identity matching is deliberately conservative.

The adapter checks exact normalized equality across candidate name/aliases/provider record id and the current AIMAN entity name/entity key/aliases. It does not perform fuzzy matching.

- zero matches -> new candidate;
- one match -> existing canonical identity;
- multiple matches -> `review_required`.

This prevents a convenient string similarity score from silently merging two real-world objects.

## Evidence policy

An OpenBot page is discovery provenance, not sufficient evidence for a canonical factual proposal.

For supported Claim hints, the adapter selects only non-OpenBot upstream sources whose extracted `supports` map contains the exact predicate/value pair. Merely linking an official page is not enough. Source preference is:

1. official page;
2. project page;
3. repository;
4. paper;
5. Hugging Face;
6. dataset/model page;
7. other upstream source.

If no upstream source explicitly supports the exact value, the hint becomes `missing_upstream_evidence`. Repository hints are the narrow exception: a repository-type source whose URL exactly equals the proposed repository URL can support that repository claim.

OpenBot readiness/confidence values remain `external_assessment` context. They are not transformed into AIMAN Claims.

## Deterministic candidates and idempotency

The candidate fingerprint is SHA-256 over normalized discovery identity, upstream sources, supported hints, and unsupported hints. Observation timestamps and external assessments do not change the candidate fingerprint.

Generated proposal idempotency keys derive from that fingerprint. Re-running the same candidate therefore produces stable proposal keys while the existing API continues to enforce its ingest idempotency boundary.

## Running locally

Given `records.json` and an optional entity-list response saved as `entities.json`:

```bash
python3 apps/agent/openbot_sensor.py records.json --entities entities.json --pack robotics --pretty
```

`records.json` can be a JSON list or `{"records": [...]}`.

`entities.json` can be a JSON list or the existing `GET /api/v1/entities` response (`{"items": [...]}`).

The command performs no network access and no writes. Its output is a plan that can be reviewed before proposal submission.

## Why v0 does not crawl OpenBot

The first integration deliberately avoids coupling the World Model to OpenBot page structure or performing whole-site replication. If OpenBot exposes a stable catalog API later, that API can become another input adapter feeding the same normalization function.

The durable contract is the AIMAN candidate and proposal boundary, not the upstream transport.

## Next proof

Use a small golden set containing:

- an already-known dataset;
- a new dataset;
- an already-known model;
- a duplicate OpenBot record;
- an identity conflict;
- a record with no upstream source;
- an OpenBot-only assessment/hint that must not become canonical.

Only after that path behaves correctly should the catalog coverage be expanded.
