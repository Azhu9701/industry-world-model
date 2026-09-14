---
name: event-extract
description: Turn public facts into first-class, evidence-backed industry events.
---

# Event extraction

Input: new public source material, existing events, and the selected pack.

1. Search existing events before creating one.
2. Classify the item as `NEW_EVENT`, `FOLLOW_UP`, or `ENRICHMENT`.
3. Use a stable event key, declared event type, precise date or explicit date precision, and resolved participants with roles.
4. Attach direct evidence and relate follow-ups to their predecessor instead of duplicating the event.
5. Keep forecasts out of events. A forecast must remain a conditional hypothesis with indicators and counterevidence.

Output an event proposal, participant proposals, and any predecessor relation for review.
