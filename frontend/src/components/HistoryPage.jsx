import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'

export default function HistoryPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.history(100)
      setItems(data.items)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const remove = async (id) => {
    await api.deleteHistory(id)
    load()
  }

  if (loading) return <p className="muted">Loading history…</p>
  if (error) return <p className="error-box">{error}</p>

  return (
    <section className="card">
      <h2>Analysis History</h2>
      {items.length === 0 ? (
        <p className="muted">No analyses yet.</p>
      ) : (
        <table className="history-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Input</th>
              <th>Text preview</th>
              <th>Prediction</th>
              <th>Confidence</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.id}>
                <td>{new Date(it.created_at * 1000).toLocaleString()}</td>
                <td>
                  <span className="tag">{it.input_type}</span>
                </td>
                <td className="preview-cell">{it.text_preview}</td>
                <td>
                  <span className={`verdict small ${it.label?.toLowerCase()}`}>
                    {it.label}
                  </span>
                </td>
                <td>{((it.confidence ?? 0) * 100).toFixed(1)}%</td>
                <td>
                  <button className="chip danger" onClick={() => remove(it.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
