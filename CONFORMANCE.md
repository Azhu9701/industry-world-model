# WORLD.md Conformance

This document defines compatibility for WORLD.md Specification v0.1.0-draft.

Conformance is intentionally lightweight. The goal is to make claims such as `WORLD.md v0.1 compatible` meaningful without forcing every domain into one schema.

## Core checklist

A WORLD.md v0.1-compatible implementation must provide discoverable answers to all six items:

- [ ] **World** — What real-world domain, environment, organization, or process is modeled?
- [ ] **Scope** — What is meaningfully inside and outside the world boundary?
- [ ] **Truth / Evidence** — Where do facts, observations, evidence, or canonical state come from?
- [ ] **Uncertainty** — How are unknown, proposed, stale, conflicting, or unverified states kept distinct when relevant?
- [ ] **Actions** — What important agent actions are read-only, proposal-only, writable, approval-gated, side-effectful, or forbidden?
- [ ] **Verification** — How can important changes be checked against declared invariants or external reality?

A project may satisfy an item directly in WORLD.md or by linking from WORLD.md to the canonical machine-readable source.

## Compatibility claim

A project that satisfies the core checklist may describe itself as:

```text
WORLD.md v0.1 compatible
```

A project with additional semantics may say:

```text
WORLD.md v0.1 compatible + <extension name>
```

A fork that changes a core requirement should not claim unqualified v0.1 compatibility.

## What conformance does not mean

Conformance does not mean:

- the represented facts are correct;
- the project is endorsed by the canonical maintainers;
- the project uses the Industry World Model runtime;
- the project uses AIMAN infrastructure;
- the project exposes write access;
- every uncertainty can be eliminated.

It only means that the world contract is discoverable and preserves the core semantics defined by the specification.

## Validation

v0.1 deliberately avoids a brittle parser that scores prose by heading names.

The first conformance mechanism is this semantic checklist plus review against real implementations.

A machine validator may be introduced after multiple independent implementations reveal which fields can be checked reliably without turning WORLD.md into a heavy configuration language.

When that validator exists, it should test portable semantics rather than one reference implementation's internal schema.

## Reference implementation mapping

The Industry World Model repository satisfies the checklist through:

- `WORLD.md` — orientation and world contract;
- `packs/<name>/domain.yaml` — ontology;
- `protocol/` — evidence-backed contribution semantics;
- reviewed canonical state — trust boundary;
- Agent/API proposal paths — action boundary;
- validators and health checks — implementation verification.

This mapping is illustrative, not mandatory.
