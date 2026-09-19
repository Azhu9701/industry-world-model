# Governance

v0.3 uses deliberately small governance.

The project optimizes for auditable factual collaboration, not voting complexity.

## Roles

### Contributor

Submits Entity identities, proposed Claims, Relations, Events, Evidence, corrections, code, or ontology changes.

### Verifier

Checks whether Evidence supports the proposed assertion, resolves conflicts, and requests additional sourcing when needed.

### Maintainer

Merges accepted contributions, protects invariants, manages canonical materialization, and handles identity merges or supersession.

### Protocol Maintainer

Maintains cross-domain protocol semantics, JSON Schemas, compatibility rules, and versioning.

## Decision unit

The unit of review is the Claim, Relation, Event, Evidence link, or protocol change — not the reputation of the person or organization submitting it.

A well-known company does not receive automatic verification. An unknown contributor is not automatically rejected.

## Conflicts

Conflicting Claims should coexist until the conflict is resolved.

Reviewers should prefer:

1. preserving both assertions and their provenance;
2. adding temporal validity;
3. adding contradicting Evidence;
4. superseding a Claim when a later world state replaces it.

Do not overwrite history simply to force one current-looking answer.

## Protocol evolution

Protocol changes require a Pull Request explaining:

- the invariant being changed;
- backward compatibility;
- migration implications;
- effects on existing packs and contributions.

Breaking changes require a protocol version change.

## What v0.3 intentionally does not use

v0.3 does not require blockchain consensus, tokens, proof-of-stake, or decentralized voting.

Those mechanisms are not necessary to prove the core collaboration loop: evidence-backed proposal, validation, review, materialization, and world-state versioning.
