# Agent operating guide

## Start here

1. Read this file, protocol/README.md, and the selected packs/<name>/domain.yaml.
2. Run ./scripts/bootstrap --pack <name> and do not proceed until ./scripts/healthcheck passes.
3. Inspect GET /api/v1/packs/<name> and confirm the runtime vocabulary matches the task.
4. Use the smallest relevant workflow in skills/*/SKILL.md.
5. Preserve provenance and the review boundary. Never write directly to PostgreSQL.
6. Run the protocol validator after changing schemas, packs, examples, or contributions.
7. Run ./scripts/healthcheck after runtime changes and language-specific checks for files you changed.

## Invariants

- Identity belongs in entities; assertions belong in claims.
- Every accepted claim, relation, event, or media asset needs public, retrievable evidence.
- Preserve conflicting claims. Do not overwrite history to manufacture one answer.
- Events are first-class. Use NEW_EVENT, FOLLOW_UP, or ENRICHMENT before generating narrative content.
- Forecasts are hypotheses with conditions and indicators, never verified events.
- Never invent sources, URLs, quotes, identifiers, dates, or images.
- Do not commit credentials or .env.

## Public contribution workflow

For Git-native contributions, create a v0.3 contribution packet under contributions/<pack>/<slug>/contribution.json.

The supported flow is:

    discover -> extract -> resolve -> evidence -> propose -> validate -> PR -> review

Rules:

- New identities may be declared as Entity objects.
- Claims, Relations, and Events require Evidence.
- Incoming factual statuses must be proposed.
- The selected pack must declare every entity type, claim predicate, relation triple, and event type.
- Stable contribution_id and idempotency_key values are required.
- Passing CI means structurally valid, not factually verified.

Run:

    python3 -m pip install -r protocol/requirements.txt
    python3 scripts/validate-contributions.py

## Deployed proposal workflow

When operating against a running instance, use the Agent/API proposal boundary:

    POST /api/v1/proposals

The Agent forwards candidates to the Rust API, which validates them against the active pack and queues them as ingest_jobs plus review_tasks.

- Entity proposals establish identity and may omit source metadata.
- Claim, relation, event, and media proposals require source metadata.
- Use a stable idempotency_key when retrying the same candidate.
- Proposal writes are disabled unless WRITE_API_ENABLED=true and IWM_WRITE_KEY is configured.
- Do not bypass review or write directly to PostgreSQL.

## Pack runtime rules

- packs/<name>/domain.yaml is executable vocabulary, not documentation.
- The pack directory name and name field must match.
- Relations may reference only entity types declared by the same pack.
- Claim predicates, event types, and relation triples must be declared before an Agent proposes them.
- Packs define vocabulary and optional seeds. They must not fork the shared core schema.
- A new pack should work with generic APIs and the web runtime without application-specific code.

## Database changes

- Add a new numbered SQL file under migrations; never edit an applied migration.
- Prefer PostgreSQL constraints over duplicate application validation.
- Keep migrations safe to replay when practical and verify with ./scripts/migrate twice.

## Scope boundaries

- protocol owns portable contribution semantics.
- packs owns domain vocabulary.
- apps/api owns persisted state, pack validation, generic read models, and deployed proposal intake.
- apps/agent discovers capabilities and proposes work; it does not bypass review.
- apps/web is a generic consumer, not the source of truth.
- skills describes focused Agent workflows.

## Checks

    python3 scripts/validate-contributions.py
    cargo test --manifest-path apps/api/Cargo.toml
    python3 -m unittest discover -s apps/agent
    npm --prefix apps/web ci
    npm --prefix apps/web run build
    docker compose config --quiet
    ./scripts/healthcheck
