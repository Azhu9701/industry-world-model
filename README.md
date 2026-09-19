# Industry World Model Framework

Build a machine-readable model of a real industry from evidence-backed entities, claims, relations, events, and time.

Industry World Model is not a website template and not a vertical database dump. The framework defines how an industry can be represented, changed, reviewed, and consumed by humans and agents.

Robotics is the first reference implementation. The same core can support manufacturing, energy, agriculture, logistics, semiconductors, biotech, or another domain by changing the domain pack instead of forking the truth model.

## Why this exists

A real industry is not one table of products.

It contains identities, assertions, relationships, events, conflicting sources, changing states, and history. Agents need those structures explicitly if they are expected to reason about an industry and eventually act inside it.

The shared model therefore separates:

- Entity — stable identity.
- Claim — an assertion about an entity.
- Evidence — why an assertion, relation, or event should be considered.
- Relation — a typed connection between entities.
- Event — a first-class change in the world.
- Snapshot — a versioned description of how accepted world state changed.

The intended loop is:

    external world
        ↓
    sensors / humans / agents
        ↓
    contribution packet
        ↓
    schema + ontology + evidence validation
        ↓
    review
        ↓
    canonical world model
        ↓
    graph / timeline / query / reasoning
        ↓
    planning and action
        ↓
    new world state

## v0.3 — World Model Contribution Protocol

v0.3 adds a Git-native public contribution contract on top of the v0.2 runtime.

A contributor does not write directly to PostgreSQL and does not get to declare a fact verified. It submits a structured packet containing proposed facts and their evidence.

The packet is checked against:

1. JSON Schema.
2. The selected domain pack ontology.
3. Relation triple rules.
4. Evidence-to-fact references.
5. The proposed-only trust boundary for incoming assertions.
6. Stable IDs and idempotency metadata.

This means a previously unknown human or Agent can submit a machine-checkable industry update without receiving database access.

See protocol/README.md and CONTRIBUTING.md.

## Quick start

Requirements: Docker with Compose, Git, curl, and Python 3.11+ for protocol validation.

    git clone https://github.com/Azhu9701/industry-world-model.git
    cd industry-world-model
    ./scripts/bootstrap --pack robotics

Validate the public contribution contract:

    python3 -m pip install -r protocol/requirements.txt
    python3 scripts/validate-contributions.py

Runtime endpoints:

- Web: http://localhost:3000
- API: http://localhost:8080/health
- Agent: http://localhost:8090/health
- Active pack: http://localhost:8080/api/v1/packs/robotics

## Architecture

    Domain Pack
    entities · claim predicates · relation triples · event types
                         ↓
              Contribution Protocol
          Entity / Claim / Evidence / Event
                         ↓
              validator + review boundary
                         ↓
               Canonical World Model
                         ↓
        PostgreSQL truth / graph / timeline
                  ↙                 ↘
             Rust API            Python Agent
                  ↘                 ↙
                    Generic Web UI

Domain packs define vocabulary. They do not fork provenance, review, identity, audit, or temporal semantics.

## Repository structure

    protocol/
      schemas/                 JSON Schema contract for v0.3
      README.md                protocol semantics and runtime mapping

    contributions/
      <pack>/<slug>/
        contribution.json      Git-native contribution packets

    examples/
      robotics/
        contribution.json      portable reference contribution
        snapshot.json          resulting world-state diff example

    packs/
      robotics/                first reference ontology
      example/                 tiny starter ontology

    apps/
      api/                     Rust truth/read-model API
      agent/                   proposal gateway for deployed instances
      web/                     generic runtime UI

    scripts/
      validate-contributions.py

## Multi-World architecture

AIMAN.World is evolving from one domain implementation into one canonical world model with multiple domain projections. Robotics is the first World; manufacturing is the next cross-world proof. Worlds reuse identity, evidence, temporal semantics, and review rather than forking truth stores.

See [docs/multi-world-architecture-v0.1.md](docs/multi-world-architecture-v0.1.md) for the architecture RFC, URL namespace plan, canonical identity migration, Robot→Manufacturing proof, and Agent Router boundary. Machine-readable planning examples live under `examples/multi-world/`.

## Domain packs

A pack declares the vocabulary that is legal for a domain.

Example:

    name: robotics

    entities:
      company:
        label: Company
      robot:
        label: Robot

    claims:
      - release_date

    relations:
      - subject: company
        predicate: manufactures
        object: robot

    events:
      - product_release

A contribution that uses an undeclared entity type, claim predicate, relation triple, or event type fails validation.

Robotics is intentionally a reference implementation, not special application code.

## Public contribution flow

    discover
      ↓
    extract
      ↓
    resolve identity
      ↓
    create Claim / Relation / Event
      ↓
    attach Evidence
      ↓
    contribution.json
      ↓
    Pull Request
      ↓
    CI validation
      ↓
    human / agent review
      ↓
    accepted contribution
      ↓
    materialization policy
      ↓
    World Snapshot

All incoming Claims, Relations, and Events must use status proposed. CI rejects contributions that attempt to self-promote to verified truth.

First-party evidence is useful evidence, but it does not bypass review.

## Deployed Agent proposal API

v0.2's deployed proposal boundary remains supported.

Agents operating against a running node can send pack-validated candidates through the Agent service. They never write directly to PostgreSQL. The Rust API stores the candidate as an ingest job and review task.

Public Git contributions and deployed API proposals are two intake surfaces for the same invariant:

> proposed information enters review before it becomes canonical world state.

## Current runtime model

The PostgreSQL core currently contains:

    Entity, Alias, Source, Claim, Evidence, Relation, Event, EventEntity,
    MediaAsset, IngestJob, ReviewTask, ChangeLog

v0.3 does not require a database migration. Protocol objects map onto the existing truth model, while Snapshot is initially an external version/diff contract. This keeps the contribution protocol independently testable before automatic materialization is introduced.

## What comes next

The immediate next step after v0.3 is not federation or token incentives.

The next proof is narrower:

> Can an independent Agent discover a real industry change, submit a valid evidence-backed packet, pass CI and review, and produce a deterministic world-state update?

Once that loop is reliable, the project can add materialization, public contribution APIs, entity resolution services, world diffs, and eventually interoperable nodes.

## License

MIT
