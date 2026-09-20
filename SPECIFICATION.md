# WORLD.md Specification

Version: 0.1.0-draft  
Status: Public draft  
Canonical project: https://github.com/Azhu9701/industry-world-model  
Canonical entry point: `WORLD.md`

WORLD.md is a plain-Markdown convention for exposing the real-world context a system models so that humans and agents can discover its scope, sources of truth, uncertainty, action boundaries, and verification path.

This specification defines the portable contract. The Industry World Model repository is a reference implementation, not the definition of the standard.

## 1. Goals

A conforming WORLD.md should let an unfamiliar human or agent answer six questions:

1. What world does this system claim to model?
2. What is in scope and out of scope?
3. Where do facts or observations come from?
4. How are unknown, conflicting, stale, or proposed facts represented?
5. What may an agent observe, propose, change, or execute?
6. How can the resulting state be verified against declared invariants or reality?

## 2. Non-goals

WORLD.md is not:

- a replacement for README.md;
- a replacement for AGENTS.md or coding instructions;
- a mandatory ontology language;
- a database schema;
- an API description format;
- a policy engine;
- a claim that every system has one perfectly knowable truth.

A WORLD.md may link to any of those systems.

## 3. Discovery

The default discovery location is `WORLD.md` at the root of a repository or world boundary.

A larger tree may contain additional WORLD.md files for narrower bounded contexts.

When more than one file applies:

1. read the parent WORLD.md for shared context;
2. read the nearest WORLD.md for the specific boundary;
3. preserve parent invariants unless the child explicitly narrows or replaces them.

## 4. Core conformance requirements

A WORLD.md v0.1-compatible implementation MUST:

1. identify the world or real-world domain being modeled;
2. communicate meaningful scope or boundaries;
3. identify sources of truth, evidence, observation, or canonical state;
4. distinguish unknown, unverified, proposed, stale, or conflicting information from accepted state where those distinctions matter;
5. describe material action boundaries when agents can produce writes or real-world side effects;
6. provide a verification path for important state changes.

The document MAY organize this information under any headings and MAY delegate details to linked machine-readable interfaces.

## 5. Reality and evidence

WORLD.md follows two baseline principles:

> Reality is upstream of the world model.

> Evidence is upstream of belief.

The internal model must not silently become more authoritative than the reality it claims to represent.

A project MAY define multiple trust levels, evidence classes, source priorities, or review states. WORLD.md should make those semantics discoverable rather than forcing a universal vocabulary.

## 6. Unknowns and disagreement

A conforming implementation must not require missing information to be converted into fabricated certainty.

Projects should preserve relevant uncertainty, conflicts, contradictions, temporal changes, and unresolved identity questions in whatever representation fits their domain.

## 7. Observation and action

WORLD.md should distinguish between surfaces that are:

- read-only;
- proposal-only;
- reversible writes;
- side-effectful writes;
- approval-gated;
- forbidden.

This requirement is intentionally semantic rather than tied to any one API, agent framework, or permission system.

## 8. Verification

Verification closes the world-model loop.

A verification path may be implemented through tests, evidence review, sensors, reconciliation jobs, checksums, signed state, human review, external APIs, physical inspection, or another domain-appropriate mechanism.

Passing a software command alone does not necessarily prove that the represented world is correct.

## 9. Interfaces

A WORLD.md may link to:

- ontologies and schemas;
- REST, GraphQL, or MCP interfaces;
- event streams;
- databases;
- CLIs;
- evidence stores;
- device or robot interfaces;
- contribution and review protocols.

The linked systems remain independently versioned unless the implementation states otherwise.

## 10. Extensions

Implementations may add domain-specific or vendor-specific sections.

Extensions MUST NOT silently redefine the meaning of core WORLD.md compatibility. If an extension changes a core requirement, that implementation should describe itself as an extension or fork rather than implying that the change is part of the canonical specification.

## 11. Versioning

The specification uses three-part versioning once stable releases begin.

- Major: breaking changes to core compatibility.
- Minor: backward-compatible additions or stronger optional guidance.
- Patch: editorial clarification that does not change conformance.

Draft releases use the suffix `-draft`.

## 12. Canonical status

The canonical specification is the version published from the canonical project history and recorded in `CHANGELOG.md`.

Copies and forks are welcome. They should preserve attribution and clearly identify local modifications when presenting themselves as derivatives of this specification.

See `ORIGIN.md`, `GOVERNANCE.md`, and `CONFORMANCE.md`.
