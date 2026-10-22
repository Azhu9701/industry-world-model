---
name: openbot-sensor
description: Convert OpenBot dataset/model discoveries into review-first AIMAN candidates without treating OpenBot as canonical evidence.
---

# OpenBot sensor

Use this skill when OpenBot surfaces a dataset or model that may belong in the robotics World Model.

## Trust boundary

OpenBot is a discovery sensor, not a source of canonical truth.

- Never bulk-copy the OpenBot catalog into canonical state.
- Never promote OpenBot readiness scores or prose into AIMAN Claims.
- Never use an OpenBot record page as the sole evidence for a factual Claim.
- A non-OpenBot URL alone is not field evidence; the source extraction must explicitly support the exact field value being proposed.
- Prefer the upstream official page, repository, paper, Hugging Face page, dataset/model page, or project page linked from the discovery record.
- Unknown, unsupported, conflicting, or unverified fields remain gaps.
- All generated facts remain proposals and pass through the existing review boundary.

## Workflow

1. Capture the OpenBot record as a discovery candidate.
2. Normalize it with `apps/agent/openbot_sensor.py`.
3. Resolve identity against current AIMAN entities using exact normalized identity only.
4. Route:
   - one exact match -> enrichment candidate;
   - no exact match -> new entity proposal;
   - multiple exact matches -> `review_required`, with no factual proposals.
5. For supported hints (`release_date`, `license`, `repository`), require a non-OpenBot upstream source that explicitly supports the exact field value before creating a Claim proposal.
6. Preserve unsupported hints and OpenBot external assessments as review context only.
7. Send resulting proposals through `/api/v1/proposals`; never write directly to PostgreSQL.

## Input shape

```json
{
  "record_type": "dataset",
  "record_id": "example-dataset",
  "record_url": "https://openbot.ai/datasets/example-dataset",
  "name": "Example Dataset",
  "aliases": ["Example-DS"],
  "upstream_sources": [
    {
      "url": "https://github.com/example/example-dataset",
      "title": "Example Dataset repository",
      "publisher": "Example Robotics",
      "source_type": "repository",
      "supports": {
        "release_date": "2026-01-05",
        "license": "Apache-2.0"
      }
    }
  ],
  "hints": {
    "release_date": "2026-01-05",
    "license": "Apache-2.0",
    "repository": "https://github.com/example/example-dataset"
  },
  "external_assessment": {
    "provider": "openbot",
    "selection_readiness": 73,
    "confidence": 0.48
  }
}
```

The adapter outputs a candidate fingerprint, identity resolution, proposals, gaps, and preserved external assessment.

## Non-goals in v0

- No OpenBot website crawler.
- No whole-catalog replication.
- No fuzzy identity merge.
- No automatic canonical write.
- No new PostgreSQL tables or robotics entity types.
- No relation proposal until both endpoints have already been resolved to canonical identities.
