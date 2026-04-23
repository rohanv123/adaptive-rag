import os
from dotenv import load_dotenv
load_dotenv()

CHUNK_SIZE    = 300
CHUNK_OVERLAP = 50
DOCS_FOLDER   = "data/documents"

EMBED_MODEL = "all-MiniLM-L6-v2"

DEFAULT_TOP_K = 5
MIN_TOP_K     = 3    # was 2 — never go below 3, you need context
MAX_TOP_K     = 10

SHORT_QUERY_WORDS   = 5
COMPLEX_QUERY_WORDS = 15
HIGH_LATENCY_MS     = 15000   # FIXED: was 800, too low for local LLM

EMA_ALPHA = 0.1   # FIXED: was 0.2, now smoother

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"   # FIXED: smaller faster model
OPENAI_KEY   = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-3.5-turbo"

CACHE_MAX_SIZE = 100