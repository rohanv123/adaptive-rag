export default function Sidebar({ history, onSelect, activeTab, setActiveTab, serverOnline }) {
  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">
          <div className="logo-icon">⚡</div>
          <span className="logo-name">AdaptRAG</span>
        </div>
        <div className="logo-version">INDICNODE ASSIGNMENT · v1.0</div>
      </div>

      <div className="sidebar-nav">
        <button
          className={`nav-item ${activeTab === "query" ? "active" : ""}`}
          onClick={() => setActiveTab("query")}
        >
          <span className="nav-icon">◈</span>
          <span className="nav-label">Query Interface</span>
        </button>
        <button
          className={`nav-item ${activeTab === "metrics" ? "active" : ""}`}
          onClick={() => setActiveTab("metrics")}
        >
          <span className="nav-icon">◎</span>
          <span className="nav-label">Performance Dashboard</span>
        </button>
      </div>

      {history.length > 0 && (
        <>
          <div className="sidebar-section-label">Recent queries</div>
          <div className="sidebar-history">
            {history.map((item, i) => (
              <div key={i} className="history-item" onClick={() => onSelect(item.query)}>
                <div className="history-query">{item.query}</div>
                <div className="history-meta">
                  {item.result?.meta?.strategy} · K={item.result?.meta?.top_k} · {Math.round(item.result?.meta?.total_ms)}ms
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="sidebar-footer">
        <div className="server-status">
          <div className={`status-dot ${serverOnline === null ? "pulse" : serverOnline ? "online" : "offline"}`} />
          <span>{serverOnline ? "Backend online" : serverOnline === false ? "Backend offline" : "Connecting..."}</span>
        </div>
      </div>
    </div>
  )
}