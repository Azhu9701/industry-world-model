# WORLD.md

A simple, open format for describing the world a system models so humans and agents can understand what exists, what is known, what is uncertain, and what actions are possible.

> Reality is upstream of the world model. Evidence is upstream of belief.

WORLD.md is intended to complement, not replace, existing project files:

- `README.md` explains what the project is.
- `AGENTS.md` explains how coding agents should work in the repository.
- `WORLD.md` explains what reality the system models and how that modeled world relates to evidence, state, change, and action.

## Status

This document is a v0.1 draft.

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

This document is distributed under the repository's MIT License.
