# WORLD.md

Version: 0.1.0-draft  
Status: Public draft  
Origin: AIMAN.World Industry World Model work (2026)  
Canonical project: https://github.com/Azhu9701/industry-world-model

A simple, open format for describing the world a system models so humans and agents can understand what exists, what is known, what is uncertain, and what actions are possible.

> Reality is upstream of the world model. Evidence is upstream of belief.

WORLD.md is intended to complement, not replace, existing project files:

- `README.md` explains what the project is.
- `AGENTS.md` explains how coding agents should work in the repository.
- `WORLD.md` explains what reality the system models and how that modeled world relates to evidence, state, change, and action.

## Status

This file is the human-facing entry point for WORLD.md Specification v0.1.0-draft.

The normative and governance suite is:

- [SPECIFICATION.md](SPECIFICATION.md) — portable requirements and versioning;
- [CONFORMANCE.md](CONFORMANCE.md) — what `WORLD.md v0.1 compatible` means;
- [GOVERNANCE.md](GOVERNANCE.md) — how the canonical specification changes;
- [ORIGIN.md](ORIGIN.md) — public origin and chronology;
- [CHANGELOG.md](CHANGELOG.md) — version history;
- [SPEC-LICENSE.md](SPEC-LICENSE.md) — CC BY 4.0 license for the specification text.

The format is intentionally small:

- plain Markdown;
- vendor-neutral;
- human-editable;
- readable by any capable agent;
- no mandatory schema language;
- no dependency on AIMAN, a specific model provider, or a specific database.

A WORLD.md may link to stricter machine-readable schemas, APIs, ontologies, evidence stores, or action interfaces. Those are implementations of the world contract, not replacements for it.

## Why WORLD.md

Agents increasingly operate across repositories, APIs, databases, devices, robots, and organizations.

Knowing how to edit the code is not enough. An agent also needs to know:

- what real-world domain this system claims to represent;
- which entities, relations, events, and states matter;
- where truth comes from;
- how uncertainty and disagreement are represented;
- what can change;
- what the agent may observe or act on;
- how a claimed change is verified against reality.

WORLD.md gives that information a predictable home.

## Core principles

### 1. Reality first

The model exists to represent or interact with reality. Do not optimize an internal representation by silently disconnecting it from the thing it claims to model.

### 2. Evidence before belief

A factual assertion should make its evidence path discoverable. Implementations should distinguish a sourced proposal from accepted canonical state.

### 3. Unknown is a valid state

Missing, conflicting, stale, or unverifiable information should remain explicit. Do not turn absence of evidence into invented certainty.

### 4. Preserve change and disagreement

When reality changes, prefer temporal updates, events, supersession, or contradiction over rewriting history to make the present look clean.

### 5. Separate observation from action

A WORLD.md should make clear what can be read, proposed, changed, executed, or written back, especially when actions have real-world side effects.

### 6. Verification completes the loop

A change is not complete merely because code ran or data was written. The system should state how an agent or human can verify that the modeled world still corresponds to reality.

### 7. The model is provisional

No ontology, schema, rule, workflow, ranking, or abstraction becomes true merely because the software depends on it.

When credible observations repeatedly contradict the model, treat that contradiction as evidence about the model. Preserve provenance, safety, and review boundaries while revising the representation.

> Reality has veto power.

A useful summary is:

> All features must conform to the shared model of reality. The model itself must continuously submit to reality.

This prevents two opposite failures: features that create parallel truths outside the shared world model, and a frozen world model that protects its own abstractions from contradictory evidence.

## Reality-first reasoning loop for agents

When an agent designs, changes, or reviews a system that claims to model reality, use this loop:

1. **Observe** — inspect the current real-world state, evidence, and known unknowns before changing abstractions.
2. **Model** — identify the entities, relations, events, constraints, and assumptions that explain the observation.
3. **Find contradictions** — look explicitly for facts that do not fit the current model. Do not hide them to preserve elegance.
4. **Act** — make the smallest change that should improve correspondence between the model and reality.
5. **Verify** — check both software invariants and the external or evidence-backed result. Green tests are necessary in many systems, but they are not proof that the world model is correct.
6. **Revise** — if reality still contradicts the model, revise the ontology, rule, assumption, or workflow rather than coercing the evidence.
7. **Repeat** — treat the new state as the next observation, not as a final answer.

This is a practical reasoning discipline:

```text
reality
  ↓
observation + evidence
  ↓
model + assumptions
  ↓
contradictions
  ↓
action
  ↓
verification
  ↓
revised model / new reality
  ↺
```

Before adding a feature, schema field, rule, or workflow, an agent should be able to answer:

- What real entity, relation, event, constraint, or uncertainty requires this?
- Where is that concept already represented in the shared world model?
- Would this change create a second source of truth or a parallel ontology?
- What evidence supports the assumption behind the change?
- What future observation would falsify that assumption?
- How are conflicting or inconvenient observations preserved?
- What external result, evidence path, or state transition will show that the change worked?
- If the model and reality disagree after the change, which part of the model is allowed to change?

Common anti-patterns include:

- **Parallel truth** — a feature invents its own copy of an entity or state instead of using the shared model.
- **Model protection** — contradictory evidence is discarded because it does not fit the current schema.
- **Test-only verification** — passing tests is treated as proof that the represented world is correct.
- **Hidden contradiction** — conflicts are normalized away instead of represented explicitly.
- **Abstraction-first development** — new layers are introduced before a recurring real-world need demonstrates them.
- **Irreversible canonization** — an assumption becomes difficult to revise merely because many features now depend on it.

The goal is not permanent instability. Stable abstractions are valuable when they continue to explain reality. The discipline is simply that internal consistency never outranks external correspondence.

## Recommended contents

WORLD.md has no required headings. A useful file will usually cover most of the following.

### World

What real-world domain, environment, organization, process, or system does this repository model?

### Scope

What is inside this world? What is explicitly outside it?

State important boundaries, time horizons, geographic or organizational limits, and known abstractions.

### Ontology

What kinds of things exist in the model?

Examples include entities, claims, relations, events, observations, assets, capabilities, constraints, and snapshots.

Link to the canonical ontology or schema if one exists.

### Sources of truth

Identify authoritative or canonical data surfaces.

Examples:

- database tables or views;
- public APIs;
- signed files;
- device or sensor output;
- evidence stores;
- reviewed Git history;
- external primary sources.

State which surface wins when two surfaces disagree.

### Evidence and trust

Describe how a claim becomes accepted.

Useful distinctions may include:

- proposed;
- observed;
- verified;
- derived;
- contradicted;
- stale;
- hypothesis;
- unknown.

These labels are examples, not mandatory vocabulary.

### State and time

Explain how current state, historical state, events, validity intervals, and snapshots are represented.

### Unknowns and conflicts

Explain how uncertainty, missing information, conflicting sources, identity ambiguity, and unresolved disputes are preserved.

### Actions

Describe the actions an agent may take in this world.

For each important action surface, make clear whether it is:

- read-only;
- proposal-only;
- reversible write;
- side-effectful write;
- approval-gated;
- forbidden.

### Verification

Describe the shortest reliable way to check whether the world model still matches its declared invariants and external reality.

### Interfaces

Link to the machine interfaces that implement the world:

- schemas;
- REST or GraphQL;
- MCP tools;
- event streams;
- CLI commands;
- databases;
- device interfaces;
- contribution protocols.

## Discovery

The default location is `WORLD.md` at the root of a repository or world boundary.

Large repositories may place additional `WORLD.md` files in subdirectories that represent more specific worlds or bounded contexts.

When multiple files apply:

1. start with the repository or parent WORLD.md for shared context;
2. apply the nearest WORLD.md for the more specific boundary;
3. do not silently discard a parent invariant unless the more specific file explicitly narrows or replaces it.

This mirrors the useful progressive-disclosure pattern of other agent-readable Markdown conventions while keeping WORLD.md focused on modeled reality rather than coding instructions.

## Minimal example

```markdown
# WORLD.md

## World

This repository models a public robotics industry graph.

## Scope

Companies, robots, parts, relations, industry events, and evidence-backed claims.

## Sources of truth

Canonical state is materialized from reviewed contributions.
Public sources provide evidence but do not write canonical state directly.

## Evidence and trust

Incoming facts are proposals.
Claims, relations, and events require evidence.
Verification happens during review and materialization.

## Unknowns and conflicts

Unknown stays unknown.
Conflicting claims are preserved rather than overwritten.

## Actions

Agents may search and propose changes.
Canonical writes require the review boundary.

## Verification

Run the contribution validator and inspect the resulting world-state diff.
```

## Relationship to schemas

WORLD.md is the orientation and contract layer.

It should tell an unfamiliar human or agent where the actual machine-readable truth lives. It is not intended to duplicate an entire ontology, API description, database schema, or policy engine in prose.

A mature implementation may look like:

```text
WORLD.md
    ↓
ontology / schemas
    ↓
evidence + state
    ↓
queries + actions
    ↓
verification
    ↓
reality
```

## Compatibility

The normative compatibility definition is maintained in [SPECIFICATION.md](SPECIFICATION.md) and [CONFORMANCE.md](CONFORMANCE.md).

An implementation can describe itself as WORLD.md-compatible when it:

1. provides a discoverable `WORLD.md`;
2. states what world is being modeled and its scope;
3. points to sources of truth or evidence;
4. makes unknown or unverified information distinguishable from canonical state;
5. describes relevant action boundaries;
6. provides a path to verification.

The format deliberately does not require a specific heading order, schema language, agent vendor, database, or runtime.

## Reference implementation

This repository, Industry World Model, is an early operational reference implementation.

Its robotics pack demonstrates one concrete mapping:

```text
Reality
  ↓
Evidence
  ↓
Entity / Claim / Relation / Event
  ↓
Contribution
  ↓
Validation + Review
  ↓
Canonical World Model
  ↓
Graph / Timeline / Query
  ↓
Agent or Human Action
  ↓
New Reality
```

The reference implementation is not the definition of the format. Other domains and implementations should be able to adopt WORLD.md without adopting this repository's ontology or runtime.

## Related work

`AGENTS.md` is a simple open format for instructions to coding agents. WORLD.md follows the same philosophy of a predictable, vendor-neutral Markdown entry point, but addresses a different question: not "how should an agent work on this repository?" but "what world does this system represent, and how is that representation grounded?"

A separate public project, [jydesign/world.md](https://github.com/jydesign/world.md), uses the WORLD.md / `.world` naming space for persistent creative-project context and visual canon. That work is related in spirit but has a different scope. This draft focuses on evidence-backed operational world models and real-world state/action boundaries.

We make no claim of priority over the WORLD.md name. Interoperability is preferable to namespace competition.

## Contributing

This is a draft, not a finished standard.

Useful contributions include:

- examples from domains outside robotics;
- counterexamples where the current concepts fail;
- simpler wording;
- interoperability notes;
- discovery semantics tested across agents;
- evidence that a proposed requirement is actually needed.

Prefer demonstrated usage over speculative complexity.

## License

The WORLD.md specification documents are licensed under CC BY 4.0 as described in [SPEC-LICENSE.md](SPEC-LICENSE.md).

The reference implementation and software remain under the repository's MIT License unless a file states otherwise.
