---
name: relation-extract
description: Extract evidence-backed relations using predicates allowed by a domain pack.
---

# Relation extraction

Input: verified source material, resolved entities, and a selected domain pack.

1. Use only subject and object entity types plus predicates declared in `domain.yaml`.
2. Capture direction exactly; `company invests_in company` is not interchangeable with its reverse.
3. Preserve validity dates and qualifiers in relation attributes.
4. Attach a source locator that directly supports both participants and the predicate.
5. Propose new entities separately when either endpoint is unresolved.

Output relation proposals. Unsupported inferences stay out of the graph.
