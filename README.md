# 🚀 Adaptive RAG System

An **Adaptive Retrieval-Augmented Generation (RAG)** system that dynamically adjusts retrieval strategy and depth at runtime to balance **accuracy, latency, and efficiency**.

Built as part of the **Indicnode Assignment**.

---

# 🧠 Overview

This system enhances traditional RAG by introducing an **adaptive decision layer** that:

* Adjusts **top-K retrieval dynamically**
* Switches between **keyword, vector, and hybrid search**
* Tracks **latency and quality metrics**
* Continuously improves using a **feedback loop**

---

# 🏗️ Architecture

<img width="1408" height="768" alt="image" src="https://github.com/user-attachments/assets/2d9938e6-1a8d-42cf-8276-082513258210" />


---

# ⚙️ Features

## ✅ Hybrid Retrieval

* Combines:

  * **Vector search (FAISS)** → semantic understanding
  * **Keyword search (BM25)** → exact matches
* Merged using **Reciprocal Rank Fusion (RRF)**

---

## ✅ Adaptive Top-K Selection

* Short queries → smaller K (faster)
* Complex queries → larger K (better context)
* High latency → reduces K automatically

---

## ✅ Query Decomposition

* Breaks complex queries into sub-queries
* Retrieves results separately and merges

---

## ✅ Cross-Encoder Reranking

* Improves relevance of retrieved chunks
* Trades slight latency for better accuracy

---

## ✅ Feedback Loop

* Tracks:

  * Latency
  * Answer quality (proxy)
* Adjusts system behavior dynamically

---

## ✅ Metrics Dashboard

* Live system performance tracking:

  * P50 / P95 latency
  * Retrieval vs generation time
  * Cache hit rate
  * Adaptive state

---

# 📊 Performance Metrics

(Example — update after running your system)

| Metric              | Value      |
| ------------------- | ---------- |
| P50 total latency   | ~21,000 ms |
| P95 total latency   | ~30,000 ms |
| Avg retrieval time  | ~500 ms    |
| Avg generation time | ~20,000 ms |
| Cache hit rate      | 0–10%      |
| Avg K selected      | ~4–5       |

---

# 🧠 Adaptive Logic

The system dynamically adjusts based on:

### Query Complexity

* ≤ 5 words → keyword + small K
* ≥ 15 words → hybrid + larger K

### Latency (EMA-based)

* High latency → reduce K
* Stable latency → maintain K

### Feedback Signals

* Low-quality answers → increase K
* Repeated failures → switch strategy

---

# ⚖️ Design Decisions & Tradeoffs

## 🔹 Why Hybrid Retrieval?

* Vector search → semantic similarity
* BM25 → exact keyword matching
* Hybrid improves overall relevance

---

## 🔹 Why Cross-Encoder?

* More accurate than bi-encoder
* Tradeoff: + latency, but better results

---

## 🔹 Why EMA (Exponential Moving Average)?

* Tracks recent latency trends
* Avoids instability from outliers
* Enables responsive adaptation

---

## 🔹 Why Adaptive K?

* Small K → faster responses
* Large K → better accuracy
* Adaptive K balances both

---

# 🚀 Setup Instructions

## 🔧 Backend

```bash
cd backend
pip install -r requirements.txt

# Pull LLM
ollama pull llama3.2:1b

# Start server
uvicorn main:app --reload
```

---

## 💻 Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🌐 Access

* API Docs:
  http://127.0.0.1:8000/docs

* Frontend UI:
  http://localhost:5173

---

# 🧪 Example Queries

* What is retrieval augmented generation?
* Compare vector search and keyword search
* Why is reranking important in RAG?
* How does adaptive top-K reduce latency?

---

# ⚠️ Limitations

* High latency due to local LLM inference (CPU)
* Quality proxy (answer length) is approximate
* No real diagram/image generation (text-based only)

---

# 🔮 Future Improvements

* GPU acceleration for faster inference
* Better quality evaluation using user feedback
* Support for diagram/image generation
* Advanced query understanding (LLM-based decomposition)

---

# 🎯 Key Takeaways

* Demonstrates **adaptive system design**
* Balances **performance vs accuracy dynamically**
* Uses **real-time metrics for optimization**
* Shows **production-level thinking in RAG systems**

---

# 📌 Conclusion

This project goes beyond a basic RAG pipeline by introducing:

👉 **Self-optimizing retrieval behavior at inference time**

---

# 👤 Author

**Rohan V**
GitHub: https://github.com/rohanv123

---
