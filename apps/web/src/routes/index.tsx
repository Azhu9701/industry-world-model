import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'

export const Route = createFileRoute('/')({ component: Home })

type Pack = {
  name: string
  title: string
  version: string
  entities: Record<string, { label?: string; fields?: string[] }>
  relations: Array<{ subject: string; predicate: string; object: string }>
  events: string[]
}

type Entity = {
  id: string
  entityType: string
  entityKey: string
  name: string
  status: string
}

type Event = {
  id: string
  eventType: string
  title: string
  occurredOn?: string | null
  status: string
}

type Runtime = {
  pack?: Pack
  entities: Entity[]
  events: Event[]
  graph: { nodes: unknown[]; edges: unknown[] }
  openReviewTasks: number
  error?: string
}

function Home() {
  const [runtime, setRuntime] = useState<Runtime>({
    entities: [],
    events: [],
    graph: { nodes: [], edges: [] },
    openReviewTasks: 0,
  })

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const base = `http://${window.location.hostname}:8080`
        const meta = await fetch(`${base}/api/v1/meta`).then((response) => response.json())
        const packName = meta.defaultPack as string
        const [pack, entities, events, graph, review] = await Promise.all([
          fetch(`${base}/api/v1/packs/${packName}`).then((response) => response.json()),
          fetch(`${base}/api/v1/entities?pack=${encodeURIComponent(packName)}&limit=12`).then((response) => response.json()),
          fetch(`${base}/api/v1/timeline?pack=${encodeURIComponent(packName)}&limit=8`).then((response) => response.json()),
          fetch(`${base}/api/v1/graph?pack=${encodeURIComponent(packName)}&limit=200`).then((response) => response.json()),
          fetch(`${base}/api/v1/review-tasks?pack=${encodeURIComponent(packName)}&limit=1`).then((response) => response.json()),
        ])
        if (!cancelled) {
          setRuntime({
            pack,
            entities: entities.items ?? [],
            events: events.items ?? [],
            graph: { nodes: graph.nodes ?? [], edges: graph.edges ?? [] },
            openReviewTasks: meta.counts?.openReviewTasks ?? review.items?.length ?? 0,
          })
        }
      } catch (error) {
        if (!cancelled) {
          setRuntime((current) => ({ ...current, error: error instanceof Error ? error.message : String(error) }))
        }
      }
    }
    void load()
    return () => { cancelled = true }
  }, [])

  const entityTypes = Object.entries(runtime.pack?.entities ?? {})

  return (
    <main>
      <p className="eyebrow">INDUSTRY WORLD MODEL · V0.2 PACK RUNTIME</p>
      <h1>{runtime.pack?.title ?? 'Build a world model'}<br />from one domain pack.</h1>
      <p className="lede">
        The selected domain pack now drives runtime validation, generic APIs, graph and timeline read models,
        and the agent proposal queue. Facts stay evidence-backed and reviewable.
      </p>

      {runtime.error ? <p className="notice">Runtime unavailable: {runtime.error}</p> : null}

      <section className="stats" aria-label="Runtime status">
        <article>
          <span>PACK</span>
          <h2>{runtime.pack?.name ?? 'loading…'}</h2>
          <p>Version {runtime.pack?.version ?? '—'}</p>
        </article>
        <article>
          <span>GRAPH</span>
          <h2>{runtime.graph.nodes.length} / {runtime.graph.edges.length}</h2>
          <p>nodes / edges in the current read model</p>
        </article>
        <article>
          <span>REVIEW</span>
          <h2>{runtime.openReviewTasks}</h2>
          <p>open tasks across evidence-backed proposals</p>
        </article>
      </section>

      <div className="flow">domain.yaml → validation → API → Agent proposal → review → graph / timeline</div>

      <div className="grid-two">
        <div>
          <p className="eyebrow">DOMAIN VOCABULARY</p>
          <div className="stack">
            {entityTypes.map(([key, definition]) => (
              <div className="row" key={key}>
                <strong>{definition.label || key}</strong>
                <span>{key}</span>
                <small>{definition.fields?.join(' · ') || 'no declared fields'}</small>
              </div>
            ))}
          </div>
        </div>
        <div>
          <p className="eyebrow">RELATIONS + EVENTS</p>
          <div className="stack">
            {(runtime.pack?.relations ?? []).slice(0, 8).map((relation) => (
              <div className="row" key={`${relation.subject}-${relation.predicate}-${relation.object}`}>
                <strong>{relation.predicate}</strong>
                <small>{relation.subject} → {relation.object}</small>
              </div>
            ))}
            {(runtime.pack?.events ?? []).slice(0, 6).map((event) => (
              <div className="row" key={event}>
                <strong>{event}</strong>
                <small>event type</small>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid-two">
        <div>
          <p className="eyebrow">ENTITIES</p>
          <div className="stack">
            {runtime.entities.length === 0 ? <p className="muted">No entities yet. Seed a pack or let an agent submit candidates.</p> : null}
            {runtime.entities.map((entity) => (
              <div className="row" key={entity.id}>
                <strong>{entity.name}</strong>
                <span>{entity.entityType}</span>
                <small>{entity.status} · {entity.entityKey}</small>
              </div>
            ))}
          </div>
        </div>
        <div>
          <p className="eyebrow">TIMELINE</p>
          <div className="stack">
            {runtime.events.length === 0 ? <p className="muted">No events yet. Event candidates require source evidence.</p> : null}
            {runtime.events.map((event) => (
              <div className="row" key={event.id}>
                <strong>{event.title}</strong>
                <span>{event.eventType}</span>
                <small>{event.occurredOn ?? 'date unknown'} · {event.status}</small>
              </div>
            ))}
          </div>
        </div>
      </div>

      <nav aria-label="Service links">
        <a href="http://localhost:8080/api/v1/packs">Pack API</a>
        <a href="http://localhost:8080/api/v1/graph">Graph API</a>
        <a href="http://localhost:8090/api/v1/capabilities">Agent capabilities</a>
      </nav>
    </main>
  )
}
