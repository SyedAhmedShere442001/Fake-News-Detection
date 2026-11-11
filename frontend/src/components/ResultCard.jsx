const SEVERITY_COLOR = {
  high: '#ff5c5c',
  medium: '#ffb84c',
  low: '#6ea8ff',
  info: '#9aa4b2',
}

function confidenceTone(label, confidence) {
  if (confidence < 0.6) return 'uncertain'
  return label?.toLowerCase()
}

export default function ResultCard({ result }) {
  const { label, confidence, probabilities, patterns, text_preview, source_url, inference_ms, model_version, disclaimer } = result
  const pct = Math.round((probabilities?.[label] ?? 0) * 100)

  return (
    <section className="card result">
      <div className="result-head">
        <h2>Prediction Result</h2>
        <span className={`verdict ${confidenceTone(label, confidence)}`}>
          {label} · {pct}%
        </span>
      </div>

      <div className="prob-bar" aria-label="Class probabilities">
        <div
          className="prob-fake"
          style={{ width: `${(probabilities?.FAKE ?? 0.5) * 100}%` }}
        />
      </div>
      <div className="prob-legend">
        <span>FAKE {(probabilities?.FAKE * 100).toFixed(1)}%</span>
        <span>REAL {(probabilities?.REAL * 100).toFixed(1)}%</span>
      </div>

      <div className="meta-row">
        <span className="tag">model: {model_version}</span>
        <span className="tag">{inference_ms} ms</span>
        {source_url && (
          <a className="tag link" href={source_url} target="_blank" rel="noreferrer">
            source
          </a>
        )}
      </div>

      {patterns?.length > 0 && (
        <div className="patterns">
          <h3>Suspicious language patterns</h3>
          <ul>
            {patterns.map((p) => (
              <li key={p.type}>
                <span
                  className="severity"
                  style={{ background: SEVERITY_COLOR[p.severity] || SEVERITY_COLOR.info }}
                />
                <div>
                  <strong>{p.description}</strong>
                  {p.matches?.length > 0 && (
                    <div className="matches">{p.matches.join(', ')}</div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <details className="preview">
        <summary>Analyzed text preview</summary>
        <p>{text_preview}</p>
      </details>

      <p className="disclaimer">{disclaimer}</p>
    </section>
  )
}
