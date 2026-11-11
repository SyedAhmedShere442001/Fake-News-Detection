import { useState } from 'react'
import { api } from '../api'
import ResultCard from './ResultCard'

export default function AnalyzePage() {
  const [mode, setMode] = useState('text')
  const [text, setText] = useState('')
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const submit = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data =
        mode === 'text' ? await api.predict(text) : await api.analyzeUrl(url)
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="analyze-grid">
      <section className="card">
        <h2>Analyze News Content</h2>
        <p className="muted">Paste article text or enter an article URL.</p>

        <div className="mode-switch">
          <button
            className={mode === 'text' ? 'chip active' : 'chip'}
            onClick={() => setMode('text')}
          >
            Text
          </button>
          <button
            className={mode === 'url' ? 'chip active' : 'chip'}
            onClick={() => setMode('url')}
          >
            Article URL
          </button>
        </div>

        {mode === 'text' ? (
          <textarea
            rows={10}
            placeholder="Paste the news article or a summary here…"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        ) : (
          <input
            type="url"
            placeholder="https://example.com/article"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        )}

        <button
          className="primary"
          disabled={loading || (mode === 'text' ? !text.trim() : !url.trim())}
          onClick={submit}
        >
          {loading ? 'Analyzing…' : 'Analyze'}
        </button>

        {error && <div className="error-box">{error}</div>}
      </section>

      {result && <ResultCard result={result} />}
    </div>
  )
}
