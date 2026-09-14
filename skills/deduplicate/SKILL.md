---
name: deduplicate
description: Identify duplicate entities while preserving uncertain candidates for human review.
---

# Deduplicate

Input: an entity proposal and existing entities plus aliases from the same pack.

1. Match exact official identifiers and canonical URLs first.
2. Then compare normalized names, aliases, manufacturer, location, and product lineage.
3. Return `same`, `different`, or `uncertain` with the fields that determined the result.
4. Auto-link only exact identifiers or canonical URLs. Send every fuzzy match to review.
5. On an approved merge, retain aliases and redirect the duplicate; never discard evidence or history.

Do not use name similarity alone to merge records.
