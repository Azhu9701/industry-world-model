# World Model Contribution Protocol v0.3.0

The protocol defines a portable, review-first way to propose changes to an Industry World Model.

It is deliberately independent from the current database implementation.

## Core objects

### Entity

Identity only. Creating an Entity says that a canonical object should exist. It does not prove arbitrary facts about that object.

### Claim

A typed assertion about an Entity. Claims carry observation time, optional validity time, status, confidence, and one or more Evidence references.

### Relation

A typed connection between two Entity references. The selected domain pack must explicitly allow the subject type, predicate, and object type triple.

### Event

A first-class change in the world. Events have stable keys, event types, classification, participants, temporal precision, and Evidence.

### Evidence

A precise source record attached to one Claim, Relation, or Event. Evidence records source provenance and whether it supports, contradicts, or only contextualizes the target.

### Snapshot

A versioned diff describing accepted change in canonical world state. Snapshots are downstream of review. Contributors submit proposals; maintainers or materialization systems create canonical snapshots.

## Trust boundary

Public contributions are proposals.

Incoming Claims, Relations, and Events must have status proposed. A contributor cannot make a fact verified merely by writing verified into JSON.

Verification is a review/materialization decision.

This rule also applies to first-party sources. A company can authoritatively state what it announced, but source identity alone does not bypass review, conflict checks, or temporal reconciliation.

## Domain compatibility

The packet's pack field selects packs/<pack>/domain.yaml.

The validator checks:

- Entity types against pack entities.
- Claim predicates against pack claims.
- Relation triples against pack relations.
- Event types against pack events.
- Evidence references against packet facts.

A contribution can reference an Entity already present in the canonical World Model without redeclaring it locally. New identities should be included in the entities array.

## Runtime mapping

The v0.3 protocol maps onto the existing v0.2 runtime without a migration:

- Entity → entities and entity_aliases.
- Claim → claims.
- Evidence.source → sources.
- Evidence → evidences.
- Relation → relations.
- Event → events and event_entities.
- Contribution metadata → ingest_jobs, review_tasks, and change_logs during materialization.

Snapshot is intentionally external in v0.3. It becomes a persisted runtime object only after the review-to-materialization contract is proven.

## Stable identifiers

Protocol IDs are portable contribution identifiers, not database UUIDs.

Examples:

    entity:robot-unitree-g1
    claim:unitree-g1-release-date
    relation:unitree-manufactures-g1
    event:unitree-g1-product-release
    evidence:unitree-g1-official-release
    contrib:unitree-g1-release-2024
    snapshot:robotics-2026-09-19

A materializer may map these IDs to internal UUIDs while preserving their external identity in audit metadata.

## Validation

Install the protocol dependencies and run:

    python3 -m pip install -r protocol/requirements.txt
    python3 scripts/validate-contributions.py

CI runs the same validation for every push and pull request.
