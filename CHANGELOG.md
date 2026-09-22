# WORLD.md Specification Changelog

This changelog tracks changes to the portable WORLD.md specification, not every runtime change in the Industry World Model reference implementation.

## Unreleased

Clarified the reality-first reasoning discipline without changing the v0.1 conformance checklist:

- the world model remains provisional and revisable under credible contradictory evidence;
- internal consistency must not be protected by suppressing or coercing observations;
- `WORLD.md` now documents an operational observe -> model -> contradiction -> act -> verify -> revise loop for agents;
- `AGENTS.md` turns that loop into concrete design and review rules, including the rule that features conform to the shared world model while the model itself remains subordinate to reality.

## 0.1.0-draft — 2026-09-20

Initial public draft.

Introduced:

- root `WORLD.md` discovery convention;
- reality-first and evidence-before-belief principles;
- explicit treatment of unknowns and conflicts;
- separation of observation, proposal, write, and side-effectful action;
- verification as part of the world-model loop;
- parent/child discovery for bounded contexts;
- vendor-neutral implementation model;
- reference implementation in Industry World Model;
- explicit origin and related-work record;
- public governance process;
- semantic v0.1 conformance checklist.

The draft intentionally does not require a schema language, fixed heading order, database, model provider, or agent runtime.
