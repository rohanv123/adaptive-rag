import { useState } from "react"

const EXAMPLES = [
  "What is retrieval augmented generation?",
  "Compare vector search and keyword search",
  "Why is re-ranking important in RAG?",
  "How does adaptive top-K reduce latency?",
]

export default function QueryBox({ onSubmit, loading }) {
  const [text, setText] = useState("")

  const submit = () => { if (text.trim()) onSubmit(text.trim()) }

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit() }
  }

  return (
    <div className="query-box">
      <div className="query-input-row">
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask a question about your documents..."
          rows={3}
          disabled={loading}
          className="query-textarea"
        />
        <button onClick={submit} disabled={loading || !text.trim()} className="query-btn">
          {loading ? (
            <span className="query-btn-loading">
              <span className="btn-spinner" />
              Thinking
            </span>
          ) : "Ask →"}
        </button>
      </div>

      <div className="examples-row">
        <span className="examples-label">TRY</span>
        {EXAMPLES.map((ex, i) => (
          <button key={i} className="example-chip"
            onClick={() => { setText(ex); onSubmit(ex) }}
            disabled={loading}>
            {ex}
          </button>
        ))}
      </div>
    </div>
  )
}