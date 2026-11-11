import { useEffect, useState } from 'react'
import { api } from './api'
import AnalyzePage from './components/AnalyzePage'
import HistoryPage from './components/HistoryPage'
import AdminPage from './components/AdminPage'

const TABS = [
  { id: 'analyze', label: 'Analyze' },
  { id: 'history', label: 'History' },
  { id: 'admin', label: 'Admin Dashboard' },
]

export default function App() {
  const [tab, setTab] = useState('analyze')
  const [health, setHealth] = useState(null)

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ status: 'offline' }))
  }, [])

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">FND</span>
          <div>
            <h1>Fake News Detector</h1>
            <p>ML classifier × pattern analysis × cloud storage</p>
          </div>
        </div>
        <div className="status">
          <span className={`dot ${health?.model_loaded ? 'ok' : 'warn'}`} />
          <span>
            {health?.status === 'offline'
              ? 'API offline'
              : health?.model_loaded
                ? `Model: ${health.model_version}`
                : 'Model not trained'}
          </span>
        </div>
      </header>

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={tab === t.id ? 'tab active' : 'tab'}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main>
        {tab === 'analyze' && <AnalyzePage />}
        {tab === 'history' && <HistoryPage />}
        {tab === 'admin' && <AdminPage />}
      </main>

      <footer className="disclaimer-banner">
        Results are automated model predictions based on statistical language
        patterns — not proof that a news story is false or true. Always verify
        with trusted primary sources.
      </footer>
    </div>
  )
}
