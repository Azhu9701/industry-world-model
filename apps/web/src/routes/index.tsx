import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({ component: Home })

const layers = [
  ['Core engine', 'Entity · Claim · Evidence · Relation · Event'],
  ['Domain packs', 'Portable vocabulary for each industry'],
  ['Agent ops', 'Discover · Extract · Verify · Review'],
]

function Home() {
  return (
    <main>
      <p className="eyebrow">OPEN SOURCE STARTER · V0.1</p>
      <h1>Build a world model<br />for any industry.</h1>
      <p className="lede">
        Start with a domain pack. Keep every fact traceable to evidence.
        Let agents grow the database without erasing uncertainty.
      </p>
      <section aria-label="Architecture layers">
        {layers.map(([title, copy], index) => (
          <article key={title}>
            <span>0{index + 1}</span>
            <h2>{title}</h2>
            <p>{copy}</p>
          </article>
        ))}
      </section>
      <div className="flow" aria-label="Knowledge flow">
        Source → Evidence → Claim / Relation / Event → API
      </div>
      <nav aria-label="Service links">
        <a href="http://localhost:8080/health">API health</a>
        <a href="http://localhost:8090/api/v1/capabilities">Agent capabilities</a>
      </nav>
    </main>
  )
}
