# AIMAN.World Multi-World Architecture v0.1

Status: Architecture RFC
Repository baseline: Industry World Model Protocol v0.3
Target evolution: protocol/runtime v0.4+
First world: `robot`
Second proof world: `manufacturing`

## 1. Decision

AIMAN.World is not a collection of independent vertical databases.

It is one canonical, evidence-backed world model with multiple domain projections called **Worlds**.

Robotics is the first World. Manufacturing is the second proof World. Compute, agriculture, logistics, energy, materials, and other domains can follow without forking identity, evidence, time, or review semantics.

The central invariant is:

> A real-world Entity, Claim, Relation, Event, or Evidence record is canonical once. Worlds classify and project it; they do not copy it into separate truth stores.

This changes the product model from:

```text
AIMAN.World = robotics website
```

into:

```text
AIMAN.World = global industrial world model
    ├── Robot World
    ├── Manufacturing World
    ├── Compute World
    ├── Agriculture World
    └── Logistics World
```

The existing `robotics` domain pack remains valid. A **pack** defines vocabulary and validation rules. A **World** defines a namespace, membership, read projection, and user/Agent entry point.

## 2. Why this is a protocol change, not only a URL change

Protocol v0.3 currently scopes canonical identity by pack:

```text
entities: UNIQUE(pack, entity_type, entity_key)
events:   UNIQUE(pack, event_key)
```

That is correct for a single-domain runtime but insufficient for Multi-World.

A company such as a robot manufacturer can simultaneously belong to Robot World and Manufacturing World. A factory-opening Event can matter to robotics, manufacturing, logistics, and compute. If each pack owns a separate copy, identity and history will drift.

Multi-World therefore requires the target model to move pack ownership out of canonical identity.

The v0.3 schemas and migrations are **not modified by this RFC**. Existing governance requires breaking protocol changes to receive a new protocol version. This document defines the target architecture and migration sequence for v0.4+.

## 3. Terminology

### 3.1 Canonical Object

A globally identified Entity, Claim, Relation, Event, or Evidence record in the shared truth model.

### 3.2 World

A named projection of the canonical model for one domain of reality.

A World has:

- a stable `world_key`;
- one primary namespace;
- one or more ontology packs;
- membership rules;
- world-specific read models and navigation;
- optional world-specific capabilities and Agent tools.

A World does **not** own a separate copy of canonical facts.

### 3.3 Domain Pack

Executable vocabulary used to validate entity types, claim predicates, relation triples, and event types.

Current example:

```text
world_key: robot
pack: robotics
namespace: /robot
```

The pack name and the public World namespace do not have to be identical.

### 3.4 WorldMembership

A statement that a canonical object is relevant to a World.

Protocol-level shape:

```json
{
  "world": "manufacturing",
  "target_kind": "entity",
  "target_id": "entity:company:unitree-robotics",
  "roles": ["manufacturer"],
  "relevance": 1.0
}
```

Runtime storage may use typed join tables rather than one polymorphic table.

### 3.5 Global Layer

Cross-world views and services over the same canonical model.

The Global Layer is not another World. It is the union and routing layer across Worlds.

## 4. Layer model

AIMAN.World should have three strict layers.

### 4.1 Protocol / Truth Layer

Owns:

- canonical identity;
- Claims;
- Relations;
- Events;
- Evidence;
- temporal validity;
- review state;
- aliases and merges;
- WorldMembership;
- snapshots and audit history.

It must not contain presentation routes or procurement execution code.

### 4.2 View / World Projection Layer

Owns:

- Global Timeline;
- World timelines;
- Global Graph;
- World graphs;
- search scopes;
- navigation;
- world landing pages;
- world-specific read models;
- SEO and canonical URLs.

It reads canonical truth and filters/projects it by WorldMembership.

It must not create competing truth.

### 4.3 Execution / Action Layer

Owns:

- AIMAN Agent Router;
- tool and connector routing;
- supplier contact;
- quotation;
- procurement;
- manufacturing execution;
- logistics execution;
- private enterprise workflows.

Actions do not mutate canonical truth directly. Their observed results return through the normal Event/Evidence/review boundary.

```text
External World
    ↓
Sensors / Humans / Agents
    ↓
Contribution + Evidence
    ↓
Canonical Truth Layer
    ↓
WorldMembership projections
    ↓
Global / Robot / Manufacturing views
    ↓
Agent Router
    ↓
Action
    ↓
Observed result → Event/Evidence → review → canonical truth
```

## 5. World registry

The initial registry is:

| world_key | Public name | Primary pack | Namespace | State |
| --- | --- | --- | --- | --- |
| `robot` | Robot World | `robotics` | `/robot` | active / first reference |
| `manufacturing` | Manufacturing World | `manufacturing` | `/manufacturing` | next proof |
| `compute` | Compute World | TBD | `/compute` | planned |
| `agriculture` | Agriculture World | TBD | `/agriculture` | planned |
| `logistics` | Logistics World | TBD | `/logistics` | planned |

The registry must be machine readable before runtime behavior depends on it.

## 6. Canonical identity

### 6.1 Compact ID

Target portable IDs should identify the object globally rather than by World:

```text
entity:company:unitree-robotics
entity:robot:unitree-g1
entity:part:example-knee-actuator
event:unitree:new-factory:2026-09
relation:unitree-g1:has-component:example-knee-actuator
```

WorldMembership is separate:

```text
entity:company:unitree-robotics
    worlds = [robot, manufacturing]
```

### 6.2 Resolvable canonical URI

Every canonical object should eventually have a stable Web URI independent of the World that displays it:

```text
https://aiman.world/id/entity/company/unitree-robotics
https://aiman.world/id/event/unitree/new-factory/2026-09
```

Human-friendly World routes may point to the same object, but the `/id/...` URI is the durable identity anchor for Agents, JSON-LD, provenance, and cross-world joins.

### 6.3 Target database shape

The v0.4 target is conceptually:

```text
entities
  id uuid pk
  canonical_key text unique
  entity_type text
  name ...

worlds
  id uuid pk
  world_key text unique
  primary_pack text
  namespace text unique

entity_world_memberships
  entity_id -> entities
  world_id  -> worlds
  roles jsonb
  relevance numeric
  unique(entity_id, world_id)

events
  id uuid pk
  canonical_key text unique
  event_type ...

event_world_memberships
  event_id -> events
  world_id -> worlds
  relevance numeric
  unique(event_id, world_id)
```

Claims and Relations can also receive explicit WorldMembership when their relevance cannot be derived safely from the participating Entities.

Evidence remains attached to the canonical fact. It is never duplicated per World.

### 6.4 Migration rule

Do not remove `pack` from existing v0.3 tables in one step.

Recommended sequence:

1. Create global canonical keys alongside existing pack-local keys.
2. Produce a collision report.
3. Resolve aliases/duplicates.
4. Add World registry and membership tables.
5. Backfill `robot` membership for current `robotics` records.
6. Move unique constraints to global canonical identity only after collision-free validation.
7. Keep origin pack in audit metadata if useful, but not as identity ownership.

## 7. Canonical Events and time

An Event exists once even when several Worlds care about it.

Example:

```text
event:company-x:new-factory:2027-03
  title: Company X opens a humanoid robot factory
  worlds:
    - robot
    - manufacturing
    - logistics
  participants:
    - entity:company:company-x
    - entity:facility:company-x-factory-2
  evidence:
    - evidence:...
```

The Global Timeline queries all accepted Events.

A World Timeline applies a WorldMembership filter:

```text
/timeline
    = all canonical Events visible to the Global Layer

/robot/timeline
    = canonical Events where world = robot

/manufacturing/timeline
    = canonical Events where world = manufacturing
```

No Event is copied into three tables or rewritten three times.

## 8. URL and information architecture

### 8.1 Global routes

These routes have cross-world semantics from now on, even while Robot is the only active World:

```text
/                 AIMAN.World global home
/timeline         Global Timeline
/graph            Global Graph
/search           Global Search
/evidence         Global Evidence explorer
/agent            Agent Router / machine entry point
/worlds           World registry and discovery
```

While only Robot World is populated, Global Timeline and Robot Timeline may return nearly the same records. Their semantics are still different and must not be implemented as separate truth stores.

### 8.2 Robot World routes

```text
/robot             Robot World home
/robot/timeline    Robot-scoped Timeline
/robot/graph       Robot-scoped Graph
/robot/search      Robot-scoped Search
/robot/evidence    Robot-scoped Evidence view
```

Existing robot detail routes such as `/robot/:robotId` can remain during the migration.

Static World control paths must be reserved before introducing them:

```text
timeline
graph
search
evidence
entities
capabilities
about
```

If an existing robot identifier collides with a reserved slug, map it explicitly before the route ships.

### 8.3 Manufacturing routes

```text
/manufacturing
/manufacturing/timeline
/manufacturing/graph
/manufacturing/search
/manufacturing/evidence
```

### 8.4 SEO / canonical behavior

Do not treat `/timeline` → `/robot/timeline` as a blind rename.

The correct semantic split is:

- `/timeline` keeps its URL and becomes the durable Global Timeline.
- `/robot/timeline` is a new scoped view.
- `/graph` keeps its URL and becomes the durable Global Graph.
- `/robot/graph` is a new scoped view.

This preserves existing links and avoids having to reclaim the old URL later when a second World exists.

Each page should self-canonicalize once its scope is materially distinct. During an initial shadow phase, new World routes may be `noindex,follow` or canonicalize to the existing global route until they have distinct scope/UI metadata.

Do not 301 `/timeline` to `/robot/timeline` if `/timeline` is intended to become Global Timeline.

### 8.5 Brand semantics

Public naming should converge on:

```text
AIMAN.World
└── Robot World
    └── 聚身之家 (Chinese historical/product alias)
```

Machine identity should prefer AIMAN.World and the World key. Human-facing Chinese pages can preserve 聚身之家 as an alias and accumulated search signal.

## 9. Robot World mapping

Robot World is not a new database. It is the first explicit WorldMembership projection over the existing robotics pack.

Initial mapping:

```text
world_key: robot
primary_pack: robotics
namespace: /robot
```

Backfill rule for current v0.3 runtime:

```text
all canonical objects whose current pack = robotics
    → candidate WorldMembership(world = robot)
```

The backfill must be reviewed for generic objects that may later belong to more than one World, especially:

- companies;
- facilities;
- AI models;
- datasets;
- open-source projects.

Those objects remain one canonical identity and can receive additional memberships later.

## 10. Manufacturing World minimum proof

Manufacturing is the preferred second World because it creates an immediate real cross-world chain rather than an isolated second catalog.

### 10.1 Minimum entity vocabulary

The first manufacturing pack should be deliberately small:

```text
company
facility
part
process
material
```

`company` and `facility` should reuse compatible global entity types already used by Robot World.

Supplier is a role of a company, not a new identity type.

### 10.2 Minimum relations

```text
robot        has_component       part
company      supplies            part
company      operates            facility
facility     supports_process    process
facility     produces            part
part         uses_material       material
```

A BOM line is represented by `has_component` plus relation attributes such as:

```json
{
  "quantity": 2,
  "position": "knee",
  "revision": "B"
}
```

### 10.3 Minimum claims

```text
capacity_per_month
lead_time_days
minimum_order_quantity
process_tolerance
facility_location
certification
unit_price_range
```

Claims remain temporal and evidence-backed. Capacity and lead time are not timeless company properties.

### 10.4 Minimum events

```text
facility_opening
capacity_change
production_start
supplier_qualification
delivery_completed
```

Delivery should be an Event, not a permanent Entity unless a later logistics model requires a durable shipment/order identity.

### 10.5 First end-to-end proof

The architecture is proven when one query can traverse:

```text
Robot
  ↓ has_component
Part / BOM line
  ↑ supplied_by (inverse of company supplies part)
Supplier Company
  ↓ operates
Factory
  ↓ supports_process
Process
  ↓ claim constraints
Capacity + lead time + MOQ
  ↓
Candidate fulfillment path
```

No duplicated Company or Part identity is allowed across Robot and Manufacturing Worlds.

## 11. Cross-world query contract

Cross-world query is a read contract over canonical identity plus World projections.

Example intent:

> Find a supplier for this humanoid knee actuator that can make 500 units with lead time <= 14 days.

Conceptual request:

```json
{
  "query_id": "query:example-knee-actuator-sourcing",
  "intent": "source_component",
  "worlds": ["robot", "manufacturing"],
  "subject": {
    "canonical_id": "entity:part:example-knee-actuator"
  },
  "constraints": [
    {"predicate": "quantity", "op": "=", "value": 500},
    {"predicate": "lead_time_days", "op": "<=", "value": 14}
  ],
  "evidence_policy": {
    "require_verified": true,
    "include_conflicts": true
  }
}
```

The query engine should:

1. resolve canonical identity;
2. determine relevant Worlds;
3. traverse shared Relations;
4. apply world-specific Claim constraints;
5. preserve Evidence and temporal validity;
6. return candidates without executing external actions.

## 12. AIMAN Agent Router model

The Agent Router sits above read models and below user/Agent intent.

```text
Intent
  ↓
World selection
  ↓
Canonical identity resolution
  ↓
Cross-world graph/query
  ↓
Constraint matching
  ↓
Decision Packet
  ↓
(optional) Action authorization
  ↓
Connector / Supplier / Factory / Logistics
  ↓
Observed result
  ↓
Event + Evidence proposal
```

The Router must not invent facts because a connector returned a successful HTTP response. Action results are observations that re-enter the evidence/review boundary.

Recommended packet boundary:

```text
World Query Packet   = what to know
Decision Packet      = what is supported and what options satisfy constraints
Action Packet        = what an authorized executor is allowed to do
Contribution Packet  = what changed in the world after the action
```

This keeps reasoning, execution, and truth updates separate.

## 13. Protocol v0.4 direction

Multi-World should be introduced as an explicit protocol version rather than silently changing v0.3 meaning.

Candidate v0.4 additions:

```text
World
WorldMembership
canonical_id / canonical_uri
world_contexts on contribution packets
world_memberships on proposed objects
cross-world identity resolution rules
```

A future contribution may look conceptually like:

```json
{
  "protocol_version": "0.4.0",
  "world_contexts": [
    {"world": "robot", "pack": "robotics"},
    {"world": "manufacturing", "pack": "manufacturing"}
  ],
  "entities": [
    {
      "id": "entity:company:example-co",
      "entity_type": "company",
      "world_memberships": ["robot", "manufacturing"]
    }
  ]
}
```

Exact JSON Schema is intentionally deferred until Phase 0 collision analysis is complete.

## 14. Phase plan

### Phase 0 — Semantics and identity inventory

No production URL behavior changes.

Deliverables:

- adopt this architecture RFC;
- add machine-readable World registry;
- reserve World keys and namespaces;
- define global canonical ID rules;
- generate current `robotics` identity/event collision inventory;
- identify route slug collisions under `/robot/*`;
- specify v0.4 migration and compatibility tests.

Acceptance:

- every current robotics Entity/Event can map to one candidate global canonical key;
- duplicate/collision list is explicit, not silently merged;
- current v0.3 validation remains green;
- no production URL or database migration is required yet.

### Phase 1 — Robot World projection

Deliverables:

- add World registry to runtime/read model;
- backfill `robot` memberships;
- expose World scope in APIs;
- add `/robot/timeline` and `/robot/graph` as filtered views;
- define `/timeline` and `/graph` as Global views;
- preserve current robot detail URLs;
- add AIMAN.World / Robot World structured identity to SEO and machine surfaces.

Acceptance:

- Global Timeline returns the same accepted Robot events as before plus world metadata;
- `/robot/timeline` equals the `world=robot` projection of the Global Timeline;
- no canonical Event or Entity is duplicated to create the new view;
- existing public links continue to resolve.

### Phase 2 — Manufacturing World proof

Deliverables:

- create `manufacturing` pack;
- add `/manufacturing` namespace;
- implement minimum entities/relations/claims/events from section 10;
- ingest at least one reviewed cross-world chain;
- prove shared Company/Facility/Part identity where applicable.

Acceptance:

- one Robot→Part→Supplier→Factory→Process→Capacity/Lead-Time path is queryable;
- the same Company ID is returned from Robot and Manufacturing scopes;
- evidence remains attached to canonical facts;
- no copy/sync job is required between Worlds.

### Phase 3 — Cross-world Router

Deliverables:

- World Query Packet contract;
- read-only cross-world query endpoint;
- Router world-selection policy;
- constraint matching over Robot + Manufacturing;
- Decision Packet with Evidence references;
- Action Packet boundary, disabled by default until explicit authorization.

Acceptance:

- one natural-language sourcing request can be decomposed into at least two Worlds;
- returned candidates cite canonical facts and Evidence;
- the Router can explain unresolved or conflicting constraints;
- no action executes during a read-only query;
- executed actions, when enabled later, re-enter the Event/Evidence review loop.

## 15. Non-goals for v0.1

This RFC does not attempt to:

- model the entire physical world;
- launch five Worlds at once;
- rename or delete existing production routes immediately;
- auto-merge similar identities;
- make Agent output canonical without review;
- place procurement/payment semantics inside the truth protocol;
- define token incentives or decentralized governance.

## 16. Architecture tests

The Multi-World design should be treated as failed if any of these become true:

1. The same company needs one canonical ID per World.
2. The same real Event is copied into multiple World tables.
3. Evidence is duplicated only so another World can display it.
4. `/robot/timeline` writes different truth than `/timeline`.
5. A pack-specific ontology change silently changes global identity.
6. Agent Router actions bypass Event/Evidence review on the return path.
7. Adding Manufacturing requires forking the canonical schema.

The desired property is the opposite:

> New Worlds add vocabulary, memberships, projections, and capabilities while reusing the same identity, evidence, time, and review substrate.

## 17. The first architectural sentence

AIMAN.World should be described internally as:

> One canonical world model, many domain Worlds, one evidence boundary, and an Agent Router that can reason and act across them.

Robot World is the first implementation of that sentence, not the final boundary of the system.
