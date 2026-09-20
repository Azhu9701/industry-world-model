# Contributing to the Industry World Model

Contributions can come from humans, organizations, or Agents. The same evidence and review rules apply to all three.

## Submit a world change

1. Select the correct domain pack in packs/.
2. Create contributions/<pack>/<short-slug>/contribution.json.
3. Give the contribution a stable contribution_id and idempotency_key.
4. Add new Entity identities only when needed.
5. Express factual assertions as Claims, Relations, or Events.
6. Attach at least one Evidence object to every Claim, Relation, and Event.
7. Keep all incoming factual statuses proposed.
8. Run the validator.
9. Open a Pull Request and explain what changed in the real world.

Validation command:

    python3 -m pip install -r protocol/requirements.txt
    python3 scripts/validate-contributions.py

## What reviewers check

Passing CI means the packet is structurally valid. It does not mean the fact is true.

Reviewers additionally check:

- identity resolution and duplicates;
- whether the source really supports the exact assertion;
- source quality and independence;
- date and temporal semantics;
- conflicts with existing Claims;
- whether an Event is new, follow-up, or enrichment;
- whether an older Claim must be superseded rather than overwritten.

## Source rules

Never invent a URL, quote, date, identifier, or source.

Use the shortest source excerpt needed to locate the evidence. Prefer locators, section names, structured selectors, or hashes over copying large passages.

First-party sources are welcome but do not automatically produce verified status. See docs/evidence-policy.md.

## Corrections

Do not rewrite history to make the current answer look clean.

When reality changes, submit a new Claim or Event and use temporal validity or supersedes semantics. When a prior assertion is wrong, submit contradicting Evidence or a correction contribution and explain the reason.

## Protocol changes

Changes to protocol/schemas, trust semantics, or governance should be isolated from ordinary industry-data contributions whenever practical. Explain compatibility impact in the Pull Request.

## WORLD.md specification changes

WORLD.md is an open specification with a separate canonical history from ordinary runtime changes.

Before proposing a normative WORLD.md change:

1. read `WORLD.md`, `SPECIFICATION.md`, `CONFORMANCE.md`, `GOVERNANCE.md`, `ORIGIN.md`, and `CHANGELOG.md`;
2. describe the real interoperability problem or implementation evidence motivating the change;
3. state whether the change is breaking, backward-compatible, or editorial;
4. update conformance language when compatibility meaning changes;
5. update `CHANGELOG.md`.

Vendor- or domain-specific experiments should begin as extensions. They become canonical only through the public specification change process.

## Synthetic examples

The OpenBot X1 contribution under contributions/robotics/_example-openbot-x1 is synthetic and exists only to keep the public contribution contract executable in CI.
