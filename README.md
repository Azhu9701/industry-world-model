# Industry World Model Starter

Turn a domain pack into an evidence-backed industry database that agents can inspect and extend.

The core flow is deliberately small:

```text
Source -> Evidence -> Claim / Relation / Event -> Timeline / Graph / API
             ^                 |
             |                 v
           Review <-------- Change log
```

`packs/robotics` is the first reference domain. Replace it with a semiconductor, energy, biotech, or other pack without rewriting the core data model.

## Quick start

Requirements: Docker with Compose, Git, and curl.

```sh
git clone https://github.com/Azhu9701/industry-world-model.git
cd industry-world-model
./scripts/bootstrap
```

Bootstrap copies `.env.example` to `.env`, builds the containers, applies migrations, starts the stack, and runs health checks.

- Web: http://localhost:3000
- API: http://localhost:8080/health
- Agent: http://localhost:8090/health

Load the example records:

```sh
./scripts/seed
```

Stop the stack with `docker compose down`. Remove local database data only when intentional with `docker compose down -v`.

PostgreSQL stays inside the Compose network by default; use `docker compose exec db psql -U iwm -d industry_world_model` for local inspection.

## What v0.1 contains

- `apps/web`: a minimal TanStack Start status page.
- `apps/api`: a Rust/Axum API with database-backed health and metadata endpoints.
- `apps/agent`: a Python standard-library service that exposes installed packs and workflow skills.
- `migrations`: the shared PostgreSQL truth model.
- `packs`: portable domain vocabulary and seed data.
- `skills`: focused instructions for discovery, extraction, verification, review, and media handling.
- `scripts`: the supported bootstrap, deploy, migrate, seed, healthcheck, and upgrade entrypoints.

## Core model

An `Entity` is identity. A `Claim` is an assertion about that identity. A `Source` is where information came from. `Evidence` binds a precise source excerpt or selector to one claim, relation, event, or media asset.

Facts are never flattened into entity columns when sources can disagree. Events are first-class records with stable `event_key` values, participants in `event_entities`, and evidence of their own. Articles and projections belong downstream; they must not silently become facts.

The initial schema includes:

```text
Entity, Alias, Claim, Source, Evidence, Relation, Event, EventEntity,
MediaAsset, IngestJob, ReviewTask, ChangeLog
```

## Domain packs

A pack declares entity types, predicates, relations, and event types in `domain.yaml`.

```yaml
name: example
entities:
  company:
    fields: [website]
relations:
  - subject: company
    predicate: produces
    object: product
events:
  - product_release
```

Keep a pack descriptive. Validation, provenance, review state, and audit behavior stay in the core engine.

## API

```text
GET /health       process and database readiness
GET /api/v1/meta  schema version and row counts
```

The agent service currently exposes read-only discovery endpoints:

```text
GET /health
GET /api/v1/capabilities
```

## Common operations

```sh
./scripts/migrate      # apply new SQL migrations once
./scripts/healthcheck  # verify all running services
./scripts/deploy       # rebuild, migrate, restart, verify
./scripts/upgrade      # fast-forward from Git, then deploy
```

## Agent handoff

Give an agent this repository and say:

> Read `AGENTS.md`, run `./scripts/bootstrap`, choose or create a domain pack, then ingest only source-backed facts through the review workflow.

## Status

v0.1 is a runnable foundation, not a finished ingestion platform. Authentication, write APIs, background queues, graph projections, and a review UI are intentionally deferred until a real domain workflow requires them.

## License

MIT
