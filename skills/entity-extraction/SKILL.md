---
name: entity-extraction
description: Extract stable entities and aliases from source material without flattening claims into identity.
---

# Entity extraction

Input: retrieved sources and `packs/<pack>/domain.yaml`.

1. Extract only entity types declared by the pack.
2. Create a stable lowercase key from the official name; keep display name and aliases separately.
3. Put descriptive values such as dimensions, dates, locations, and ownership into proposed claims, not entity columns.
4. Preserve source wording and language in aliases; normalize a separate lookup value.
5. Send ambiguous identity matches to deduplication or review.

Output entity and alias proposals with source IDs. Never merge or verify them automatically.
