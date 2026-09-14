# Industry World Model Starter

Turn a small domain pack into an evidence-backed industry database that agents can inspect, extend, and deploy.

The core flow is deliberately small:

```text
domain.yaml
    ↓
Pack runtime validation
    ↓
Source -> Evidence -> Claim / Relation / Event -> Timeline / Graph / API
             ^                 |
             |                 v
           Review <----- Agent proposals
```

`packs/robotics` is the first reference domain. Replace it with semiconductor, energy, biotech, manufacturing, or another pack without forking the core data model.

## Quick start

Requirements: Docker with Compose, Git, and curl.

```sh
git clone https://github.com/Azhu9701/industry-world-model.git
cd industry-world-model
./scripts/bootstrap --pack robotics
```

Or start with the tiny example pack:

```sh
./scripts/bootstrap --pack example
./scripts/seed
```

Bootstrap copies `.env.example` to `.env`, selects the requested pack, builds the containers, applies migrations, validates the pack at API startup, starts the stack, and runs health checks.

- Web: http://localhost:3000
- API: http://localhost:8080/health
- Agent: http://localhost:8090/health
- Active pack: http://localhost:8080/api/v1/packs/<pack>

Stop the stack with `docker compose down`. Remove local database data only when intentional with `docker compose down -v`.

## What v0.2 changes

v0.2 makes domain packs executable instead of descriptive-only configuration.

- The API loads and validates `DEFAULT_PACK` at startup.
- `domain.yaml` controls accepted entity types, claim predicates, relation triples, and event types.
- Generic entity, relation, event, timeline, graph, review, and pack endpoints work for every pack.
- The web app reads the active pack at runtime instead of hard-coding robotics or example fields.
- The Python agent can submit pack-validated candidates to the Rust API without direct database access.
- Candidate writes are review-first and disabled by default.
- `./scripts/bootstrap --pack <name>` and `./scripts/seed` follow the selected pack.

## Architecture

```text
┌────────────────────────────────────────────┐
│ Domain pack                                │
│ entities · claims · relations · events     │
└──────────────────────┬─────────────────────┘
                       ↓
┌────────────────────────────────────────────┐
│ Rust API / Pack Runtime                    │
│ validate · read models · proposal gateway  │
└──────────────┬─────────────────┬───────────┘
               ↓                 ↓
        PostgreSQL truth     Python Agent
               ↓                 ↓
 entity/claim/evidence     skills + proposals
 relation/event/review           │
               └──────────┬───────┘
                          ↓
                  TanStack generic UI
```

## Core model

An `Entity` is identity. A `Claim` is an assertion about that identity. A `Source` is where information came from. `Evidence` binds a precise source excerpt or selector to one claim, relation, event, or media asset.

Facts are never flattened into entity columns when sources can disagree. Events are first-class records with stable `event_key` values, participants in `event_entities`, and evidence of their own. Articles and projections belong downstream; they must not silently become facts.

The shared schema includes:

```text
Entity, Alias, Claim, Source, Evidence, Relation, Event, EventEntity,
MediaAsset, IngestJob, ReviewTask, ChangeLog
```

## Domain packs

A pack declares its vocabulary in `packs/<name>/domain.yaml`.

```yaml
name: example
title: Example Industry
version: 0.2.0

entities:
  company:
    label: Company
    fields: [website]
  product:
    label: Product
    fields: [release_date]

claims: [website, release_date]

relations:
  - subject: company
    predicate: produces
    object: product

events: [product_release]
```

At runtime the API rejects malformed packs, relations that reference unknown entity types, duplicate vocabulary entries, and proposal kinds that are not declared by the selected pack.

Keep a pack descriptive. Provenance, review state, audit behavior, identity rules, and the shared PostgreSQL schema stay in the core engine.

## Read API

```text
GET /health
GET /api/v1/meta
GET /api/v1/packs
GET /api/v1/packs/:pack
GET /api/v1/entities?pack=<pack>&entity_type=<type>
GET /api/v1/entities/:id
GET /api/v1/relations?pack=<pack>
GET /api/v1/events?pack=<pack>
GET /api/v1/timeline?pack=<pack>
GET /api/v1/graph?pack=<pack>
GET /api/v1/review-tasks?pack=<pack>
```

The graph endpoint is a generic read model derived from entities and relations. The timeline endpoint is a generic read model derived from first-class events.

## Agent proposal API

Agents never write directly to PostgreSQL. They submit a pack-validated candidate to the API, which stores it as an `ingest_job`, creates a `review_task`, and records a `change_log` entry.

Writes are off by default. To enable them locally, set:

```env
WRITE_API_ENABLED=true
IWM_WRITE_KEY=replace-with-a-random-local-secret
```

Then an agent can call the Python gateway:

```text
POST http://localhost:8090/api/v1/proposals
```

Example event candidate:

```json
{
  "pack": "robotics",
  "kind": "event",
  "payload": {
    "event_type": "product_release",
    "title": "Example release candidate"
  },
  "source": {
    "url": "https://example.com/official-release",
    "title": "Official release"
  },
  "idempotency_key": "example-release-2026-01"
}
```

Claim, relation, event, and media proposals require source metadata. Entity proposals may be submitted without source evidence because they establish identity rather than asserting a verified fact.

v0.2 intentionally queues candidates for review instead of auto-materializing them into verified facts. Review decisions and materialization policy can evolve without giving agents direct database write access.

## Agent handoff

Give an agent this repository and say:

> Read `AGENTS.md`. Run `./scripts/bootstrap --pack robotics` (or create a new domain pack), inspect `/api/v1/packs/<pack>`, then use the focused skills to discover, extract, verify, and submit evidence-backed candidates through the proposal endpoint. Never write directly to PostgreSQL.

## Common operations

```sh
./scripts/bootstrap --pack robotics
./scripts/migrate
./scripts/seed
./scripts/healthcheck
./scripts/deploy
./scripts/upgrade
```

## v0.2 boundary

This release establishes the pack runtime and review-first proposal boundary. It does **not** yet auto-materialize approved proposals, provide authentication for multi-user public deployments, run background ingestion queues, or render an interactive force-directed graph. Those belong after the review/materialization contract is proven against real domain workflows.

## License

MIT
