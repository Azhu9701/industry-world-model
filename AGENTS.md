# Agent operating guide

## Start here

1. Read this file and the selected `packs/<name>/domain.yaml`.
2. Run `./scripts/bootstrap --pack <name>` and do not proceed until `./scripts/healthcheck` passes.
3. Inspect `GET /api/v1/packs/<name>` and confirm the runtime vocabulary matches the task.
4. Use the smallest relevant workflow in `skills/*/SKILL.md`.
5. Submit candidates through the Agent/API proposal boundary. Never write directly to PostgreSQL.
6. Run `./scripts/healthcheck` after changes. Run language-specific checks for files you changed.

## Invariants

- Identity belongs in `entities`; assertions belong in `claims`.
- Every accepted claim, relation, event, or media asset needs public, retrievable evidence.
- Preserve conflicting claims. Do not overwrite history to manufacture one answer.
- Events are first-class. Use `NEW_EVENT`, `FOLLOW_UP`, or `ENRICHMENT` before generating narrative content.
- Forecasts are hypotheses with conditions and indicators, never verified events.
- Never invent sources, URLs, quotes, identifiers, dates, or images.
- Do not commit credentials or `.env`.

## Pack runtime rules

- `packs/<name>/domain.yaml` is executable vocabulary, not documentation.
- The pack directory name and `name:` field must match.
- Relations may reference only entity types declared by the same pack.
- Claim predicates, event types, and relation triples must be declared before an agent proposes them.
- Packs define vocabulary and optional seeds. They must not fork the shared core schema.
- A new pack should work with the generic APIs and web runtime without application-specific code.

## Proposal workflow

The supported v0.2 flow is:

```text
discover -> extract -> verify -> propose -> review
```

The Agent service accepts candidates at:

```text
POST /api/v1/proposals
```

The Agent forwards them to the Rust API, which validates them against the active pack and queues them as `ingest_jobs` plus `review_tasks`.

- Entity proposals establish identity and may omit source metadata.
- Claim, relation, event, and media proposals require source metadata.
- Use a stable `idempotency_key` when retrying the same candidate.
- Proposal writes are disabled unless `WRITE_API_ENABLED=true` and `IWM_WRITE_KEY` is configured.
- v0.2 does not auto-materialize a review candidate into verified truth. Do not bypass that boundary.

## Database changes

- Add a new numbered SQL file under `migrations`; never edit an applied migration.
- Prefer PostgreSQL constraints over duplicate application validation.
- Keep migrations safe to replay when practical and verify with `./scripts/migrate` twice.

## Scope boundaries

- `apps/api` owns persisted state, pack validation, generic read models, and the proposal boundary.
- `apps/agent` discovers capabilities and proposes work; it does not bypass review or write directly to PostgreSQL.
- `apps/web` is a generic consumer of the runtime API, not the source of truth.
- `packs` define domain vocabulary; they do not fork the core schema.
- `skills` describe focused agent workflows and must preserve the provenance/review invariants above.

## Checks

```sh
cargo test --manifest-path apps/api/Cargo.toml
python3 -m unittest discover -s apps/agent
npm --prefix apps/web ci
npm --prefix apps/web run build
docker compose config --quiet
./scripts/healthcheck
```
