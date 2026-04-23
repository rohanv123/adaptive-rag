import { useState, useCallback, useEffect } from "react"
import QueryBox from "./components/QueryBox"
import ResultPanel from "./components/ResultPanel"
import MetricsDashboard from "./components/MetricsDashboard"
import Sidebar from "./components/Sidebar"
import "./App.css"

const API = "http://localhost:8000"

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [queryText, setQueryText] = useState("")
  const [history, setHistory] = useState([])
  const [activeTab, setActiveTab] = useState("query")
  const [serverOnline, setServerOnline] = useState(null)

  useEffect(() => {
    fetch(`${API}/health`).then(r => r.json())
      .then(d => setServerOnline(d.chunks > 0))
      .catch(() => setServerOnline(false))
  }, [])

  const handleQuery = useCallback(async (query) => {
    setLoading(true)
    setError(null)
    setQueryText(query)
    setActiveTab("query")

    try {
      const res = await fetch(`${API}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const data = await res.json()
      setResult(data)
      setHistory(h => [{ query, result: data, ts: Date.now() }, ...h].slice(0, 20))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleRating = useCallback(async (rating) => {
    if (!queryText) return
    await fetch(`${API}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryText, rating })
    })
  }, [queryText])

  return (
    <div className="app-shell">
      <Sidebar
        history={history}
        onSelect={(q) => handleQuery(q)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        serverOnline={serverOnline}
      />

      <div className="main-content">
        <div className="topbar">
          <div className="topbar-left">
            <span className="breadcrumb">
              {activeTab === "query" ? "Query Interface" : "Performance Dashboard"}
            </span>
          </div>
          <div className="topbar-right">
            <div className={`status-dot ${serverOnline === null ? "pulse" : serverOnline ? "online" : "offline"}`} />
            <span className="status-label">
              {serverOnline === null ? "Connecting..." : serverOnline ? "Backend connected" : "Backend offline"}
            </span>
          </div>
        </div>

        {activeTab === "query" ? (
          <div className="query-view">
            <div className="hero">
              <div className="hero-tag">Adaptive RAG · Level 3</div>
              <h1 className="hero-title">Intelligent Document<br /><span className="accent">Retrieval System</span></h1>
              <p className="hero-sub">Hybrid vector + keyword search · Dynamic K · Real-time adaptation</p>
            </div>

            <QueryBox onSubmit={handleQuery} loading={loading} />

            {error && (
              <div className="error-card">
                <div className="error-icon">!</div>
                <div>
                  <div className="error-title">Connection Error</div>
                  <div className="error-msg">{error}</div>
                </div>
              </div>
            )}

            {loading && (
              <div className="thinking-card">
                <div className="thinking-dots">
                  <span /><span /><span />
                </div>
                <div className="thinking-text">Retrieving and generating answer...</div>
              </div>
            )}

            {result && !loading && (
              <ResultPanel result={result} onRate={handleRating} />
            )}
          </div>
        ) : (
          // ✅ FIXED HERE
          <MetricsDashboard 
            apiBase={API} 
            isActive={activeTab === "metrics"} 
          />
        )}
      </div>
    </div>
  )
}