import { useState } from "react"

export default function ResultPanel({ result, onRate }) {
  const [rated, setRated] = useState(false)
  const [hovered, setHovered] = useState(0)
  const m = result.meta

  const handleRate = (s) => { if (!rated) { onRate(s); setRated(true) } }

  const latencyColor = (ms) => ms < 1000 ? "green" : ms < 3000 ? "amber" : "red"
  const strategyColor = (s) => s === "hybrid" ? "accent" : s === "vector" ? "green" : "amber"

  return (
    <div className="result-panel">

      <div className="result-header">
        <div className="result-header-left">
          <span className="result-label">Answer</span>
          {m.cache_hit && <span className="cache-badge">CACHE HIT</span>}
        </div>
        <span className="result-label">{new Date().toLocaleTimeString()}</span>
      </div>

      <div className="answer-body">
        <p className="answer-text">{result.answer}</p>
      </div>

      <div className="meta-strip">
        <div className="meta-cell">
          <div className="meta-cell-label">Strategy</div>
          <div className={`meta-cell-value ${strategyColor(m.strategy)}`}>{m.strategy}</div>
        </div>
        <div className="meta-cell">
          <div className="meta-cell-label">Top-K</div>
          <div className="meta-cell-value accent">{m.top_k}</div>
        </div>
        <div className="meta-cell">
          <div className="meta-cell-label">Complexity</div>
          <div className="meta-cell-value">{m.complexity}</div>
        </div>
        <div className="meta-cell">
          <div className="meta-cell-label">Retrieval</div>
          <div className={`meta-cell-value ${latencyColor(m.retrieval_ms)}`}>
            {Math.round(m.retrieval_ms)}ms
          </div>
        </div>
        <div className="meta-cell">
          <div className="meta-cell-label">Generation</div>
          <div className={`meta-cell-value ${latencyColor(m.generation_ms)}`}>
            {Math.round(m.generation_ms)}ms
          </div>
        </div>
        <div className="meta-cell">
          <div className="meta-cell-label">Total</div>
          <div className={`meta-cell-value ${latencyColor(m.total_ms)}`}>
            {Math.round(m.total_ms)}ms
          </div>
        </div>
      </div>

      <div className="decision-bar">
        <span className="decision-icon">⚙</span>
        <span className="decision-label">ADAPTIVE DECISION</span>
        <span className="decision-value">{m.reason}</span>
      </div>

      {result.sources?.length > 0 && (
        <div className="sources-section">
          <div className="sources-title">Sources retrieved ({result.sources.length})</div>
          {result.sources.map((s, i) => (
            <div key={i} className="source-card">
              <div className="source-idx">[{i + 1}]</div>
              <div className="source-content">
                <div className="source-file">{s.file}</div>
                <div className="source-preview">{s.preview}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="rating-section">
        {rated ? (
          <span className="rating-thanks">Thanks — system will adapt from your feedback.</span>
        ) : (
          <>
            <span className="rating-label">Rate this answer:</span>
            <div className="star-row">
              {[1,2,3,4,5].map(s => (
                <button key={s}
                  className={`star ${s <= hovered ? "active" : ""} ${rated ? "rated" : ""}`}
                  onMouseEnter={() => !rated && setHovered(s)}
                  onMouseLeave={() => !rated && setHovered(0)}
                  onClick={() => handleRate(s)}>★</button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}