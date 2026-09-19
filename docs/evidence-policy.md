# Evidence Policy

Evidence is the trust layer of the Industry World Model.

The goal is not to label an entire website trustworthy or untrustworthy. The goal is to record why a specific Claim, Relation, or Event is supported, contradicted, or contextualized.

## Source types

The v0.3 protocol recognizes:

- first_party — the company, project, person, or organization speaking about itself;
- government — government publication or public authority;
- regulator — exchange, regulator, filing system, or formal registry;
- academic — paper, institution, or research publication;
- repository — source-code or dataset repository;
- media — editorial or journalistic publication;
- database — structured third-party database;
- other — a source that does not fit the above classes.

Source type is provenance, not a truth score.

## First-party evidence

First-party material is often the best source for what an organization announced, released, published, or claims about itself.

It is not automatically verified truth.

A contribution backed only by first-party evidence still enters as proposed and passes through review. High-impact, contested, quantitative, or third-party-effect Claims should seek independent corroboration where practical.

## Evidence must bind to a precise fact

Evidence attaches to one Claim, Relation, or Event.

Prefer a precise locator, section, selector, timestamp, table row, or short excerpt. Avoid attaching a homepage to a highly specific fact when a more precise source exists.

The evidence stance must be explicit:

- supports;
- contradicts;
- context.

Contradicting evidence should be preserved rather than deleted.

## Time matters

Record when a source was published when known and when it was captured.

A source can be historically correct and currently superseded. Review should preserve that history instead of silently replacing old facts.

## Copyright and source preservation

Store only the minimum excerpt needed for verification. Prefer source locators and hashes over reproducing long copyrighted text.

Do not mirror restricted material merely to make validation convenient.

## Review outcome

Schema-valid evidence is not the same thing as sufficient evidence.

Verification remains a review decision based on the exact Claim, source quality, conflicts, temporal context, and the domain's evidence expectations.
