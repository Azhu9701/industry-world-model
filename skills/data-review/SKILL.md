---
name: data-review
description: Review proposed entities, facts, relations, events, and media before acceptance.
---

# Data review

Input: one review task, its target record, domain pack, sources, and evidence.

1. Check pack vocabulary, identity resolution, direct evidence, dates, units, status, and duplicate risk.
2. Compare active conflicting claims rather than overwriting them.
3. Decide `approved`, `rejected`, or `changes_requested` with a concise reason.
4. Require a change-log entry containing actor, target, before and after state, and reason.
5. Apply decisions only through the core API transaction once that write endpoint exists.

Until a reviewed write API ships, produce a review decision without mutating PostgreSQL.
