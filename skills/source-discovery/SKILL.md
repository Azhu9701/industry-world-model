---
name: source-discovery
description: Find authoritative public sources for a domain-pack research target.
---

# Source discovery

Input: a precise entity, claim, relation, or event question and a selected domain pack.

1. Search first-party product pages, filings, documentation, repositories, and official announcements first.
2. Add independent primary reporting only when it contributes a distinct fact or resolves ambiguity.
3. Record the canonical URL, title, publisher, publication date when present, access time, and source type.
4. Return gaps explicitly. Never invent a URL or use a search-result snippet as evidence.

Output source candidates only; do not mark facts verified or write directly to PostgreSQL.
