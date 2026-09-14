# Agent operating guide

## Start here

1. Read this file and the selected `packs/<name>/domain.yaml`.
2. Run `./scripts/bootstrap` and do not proceed until `./scripts/healthcheck` passes.
3. Use the smallest relevant workflow in `skills/*/SKILL.md`.
4. Run `./scripts/healthcheck` after changes. Run language-specific checks for files you changed.

## Invariants

- Identity belongs in `entities`; assertions belong in `claims`.
- Every accepted claim, relation, event, or media asset needs public, retrievable evidence.
- Preserve conflicting claims. Do not overwrite history to manufacture one answer.
- Events are first-class. Use `NEW_EVENT`, `FOLLOW_UP`, or `ENRICHMENT` before generating narrative content.
- Forecasts are hypotheses with conditions and indicators, never verified events.
- Never invent sources, URLs, quotes, identifiers, dates, or images.
- Do not commit credentials or `.env`.

## Database changes

- Add a new numbered SQL file under `migrations`; never edit an applied migration.
- Prefer PostgreSQL constraints over duplicate application validation.
- Keep migrations safe to replay when practical and verify with `./scripts/migrate` twice.

## Scope boundaries

- `apps/api` owns persisted state and validation.
- `apps/agent` proposes work; it does not bypass review or write directly to PostgreSQL.
- `apps/web` is a consumer, not the source of truth.
- `packs` define domain vocabulary; they do not fork the core schema.

## Checks

```sh
cargo test --manifest-path apps/api/Cargo.toml
python3 -m unittest discover -s apps/agent
npm --prefix apps/web run build
docker compose config --quiet
./scripts/healthcheck
```
