import { useEffect, useState } from "react";

export default function MetricsDashboard({ apiBase, isActive }) {
  const [metrics, setMetrics] = useState(null);

  const fetchMetrics = async () => {
    try {
      const res = await fetch(`${apiBase}/metrics`);
      const data = await res.json();
      setMetrics(data);
    } catch (err) {
      console.error("Error fetching metrics:", err);
    }
  };

  // ✅ FIX: fetch when tab becomes active
  useEffect(() => {
    if (isActive) {
      fetchMetrics();

      const interval = setInterval(fetchMetrics, 3000);
      return () => clearInterval(interval);
    }
  }, [isActive]);

  if (!metrics || !metrics.count) {
    return (
      <div style={{ padding: "20px" }}>
        <h3>Performance Dashboard</h3>
        <p>No data yet — run some queries first.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "20px" }}>
      <h3>Performance Dashboard</h3>

      <p><b>Total Queries:</b> {metrics.count}</p>
      <p><b>P50 Latency:</b> {metrics.total_latency?.p50_ms} ms</p>
      <p><b>P95 Latency:</b> {metrics.total_latency?.p95_ms} ms</p>
      <p><b>Avg Retrieval:</b> {metrics.retrieval_latency?.mean_ms} ms</p>
      <p><b>Avg Generation:</b> {metrics.generation_latency?.mean_ms} ms</p>
      <p><b>Cache Hit Rate:</b> {((metrics.cache?.hit_rate || 0) * 100).toFixed(1)}%</p>
      <p><b>Average K:</b> {metrics.avg_k}</p>

      <h4>Adaptive State</h4>
      <p><b>Strategy:</b> {metrics.adaptive_state?.strategy}</p>
      <p><b>Current K:</b> {metrics.adaptive_state?.current_k}</p>
      <p><b>Avg Latency (EMA):</b> {metrics.adaptive_state?.avg_latency_ms} ms</p>
    </div>
  );
}