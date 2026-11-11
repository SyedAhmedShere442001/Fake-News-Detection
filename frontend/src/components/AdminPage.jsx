import { useEffect, useState } from 'react'
import { api } from '../api'

function BarChart({ data, colorA = '#ff5c5c', colorB = '#4ade80' }) {
  const entries = Object.entries(data || {})
  const max = Math.max(1, ...entries.map(([, v]) => v))
  if (entries.length === 0) return <p className="muted">No activity yet.</p>
  return (
    <div className="bar-chart">
      {entries.map(([day, count]) => (
        <div className="bar-col" key={day}>
          <div className="bar-wrap">
            <div
              className="bar"
              style={{ height: `${(count / max) * 100}%`, background: colorB }}
              title={`${count} analyses`}
            />
          </div>
          <span className="bar-label">{day.slice(5)}</span>
        </div>
      ))}
    </div>
  )
}

function LabelSplit({ by_label, total }) {
  const fake = by_label?.FAKE ?? 0
  const real = by_label?.REAL ?? 0
  const unknown = by_label?.UNKNOWN ?? 0
  const pct = (n) => (total ? (n / total) * 100 : 0)
  return (
    <div>
      <div className="prob-bar tall">
        <div className="prob-fake" style={{ width: `${pct(fake)}%` }} />
        {unknown > 0 && (
          <div className="prob-unknown" style={{ width: `${pct(unknown)}%` }} />
        )}
      </div>
      <div className="prob-legend">
        <span>FAKE {fake}</span>
        <span>{unknown > 0 && <>UNKNOWN {unknown} · </>}REAL {real}</span>
      </div>
    </div>
  )
}

export default function AdminPage() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.analytics().then(setData).catch((e) => setError(e.message))
  }, [])

  if (error) return <p className="error-box">{error}</p>
  if (!data) return <p className="muted">Loading dashboard…</p>

  return (
    <div className="admin-grid">
      <section className="card stat">
        <h3>Total analyses</h3>
        <div className="stat-value">{data.total}</div>
      </section>
      <section className="card stat">
        <h3>Avg. confidence</h3>
        <div className="stat-value">
          {((data.avg_confidence ?? 0) * 100).toFixed(1)}%
        </div>
      </section>
      <section className="card stat">
        <h3>Storage backend</h3>
        <div className="stat-value small">{data.storage}</div>
      </section>

      <section className="card">
        <h3>Prediction distribution</h3>
        <LabelSplit by_label={data.by_label} total={data.total} />
      </section>

      <section className="card">
        <h3>Analyses per day</h3>
        <BarChart data={data.by_day} />
      </section>
    </div>
  )
}
