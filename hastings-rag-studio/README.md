# 🧠 Hastings RAG Studio

> *Your documents. Your knowledge. Your intelligence.*

[![Live Demo](https://img.shields.io/badge/Live%20Demo-hastings--rag--studio.onrender.com-brightgreen)](https://hastings-rag-studio.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.45-red)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A professional **Document Intelligence and Agentic RAG platform** built by Hastings AI. Upload documents, ask questions, and receive evidence-grounded answers with full citations — powered by a full advanced RAG pipeline.

**[→ Try the live demo](https://hastings-rag-studio.onrender.com)**

---

## ✨ Features

### Core RAG Pipeline
- 📄 **Multi-format ingestion** — PDF (with page numbers), DOCX, TXT, Markdown
- 🔍 **Hybrid retrieval** — Vector search + BM25 keyword search merged with Reciprocal Rank Fusion (RRF)
- 🎯 **Cross-encoder reranking** — Precision reranking of top candidates
- 🔄 **Query rewriting** — LLM-powered query expansion for better retrieval
- ✂️ **Context compression** — Trims irrelevant sentences before generation to reduce token usage
- 💬 **Grounded generation** — Groq LLM answers only from retrieved evidence
- 📚 **Citations** — Every claim mapped to [S1], [S2] with filename and page number
- ✅ **Citation verification** — Flags unsupported statements automatically using embedding similarity

### Intelligence & Evaluation
- 🔬 **RAG Intelligence Lab** — Inspect every pipeline step with per-stage latency metrics
- 📊 **Evaluation dashboard** — Precision@k, Recall@k, MRR against labelled test sets
- 💾 **Persistent chat history** — Conversations saved to PostgreSQL, exportable as Markdown/JSON
- 🔧 **Model selector** — Switch Groq models from the UI without restarting

### Infrastructure
- 🗄️ **PostgreSQL + pgvector** — HNSW index for fast approximate nearest-neighbour search
- 🐳 **Docker** — Multi-stage build, models pre-baked into the image for zero cold-start
- ☁️ **Render + Neon** — Free-tier cloud deployment included

---

## 🏗️ Architecture

```
User Question
     │
     ▼
Query Rewriting (Groq LLM)
     │
     ▼
┌────────────────────────────────┐
│  Hybrid Retrieval              │
│  ├── Vector Search (pgvector)  │
│  └── BM25 Keyword Search       │
│          └── RRF Fusion        │
└────────────────────────────────┘
     │
     ▼
Cross-Encoder Reranking
     │
     ▼
Context Compression
     │
     ▼
Groq LLM Generation
     │
     ▼
Citation Verification
     │
     ▼
Answer + Sources + Evidence
```

---

## 🚀 Quick Start

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Docker | Any recent version |
| WSL 2 | Ubuntu 20.04+ recommended |

### Local Setup (WSL / Linux)

**1. Start PostgreSQL with pgvector:**
```bash
docker run --name hastings-pg \
  -e POSTGRES_PASSWORD=YOUR_PASSWORD \
  -e POSTGRES_DB=hastings_rag \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
```

**2. Clone and set up:**
```bash
git clone https://github.com/hastingsdata072-ctrl/hastings-rag-studio.git
cd hastings-rag-studio
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Configure:**
```bash
cp .env.example .env
# Edit .env and fill in GROQ_API_KEY and DATABASE_URL
```

**4. Initialise database:**
```bash
python scripts/init_db.py
```

**5. Run:**
```bash
streamlit run app.py --server.fileWatcherType none
```

Open [http://localhost:8501](http://localhost:8501)

> **Note:** All development and testing was done on WSL 2 (Ubuntu). Running natively on Windows without WSL is not tested and not recommended.

---

## ☁️ Cloud Deployment

The app is deployed on **Render** (free tier) with **Neon** (serverless PostgreSQL + pgvector).

### Deploy your own instance

1. Fork this repository
2. Create a free Neon database at [neon.tech](https://neon.tech) and run `scripts/init_db.py` against it
3. Create a free Web Service on [render.com](https://render.com) connected to your fork
4. Add environment variables (see `.env.example`)
5. Deploy — Render uses the `Dockerfile` automatically

---

## 🗂️ Project Structure

```
hastings-rag-studio/
├── app.py                      # Streamlit entry point (7 pages)
├── requirements.txt
├── Dockerfile
├── render.yaml                 # Render deployment config
├── .env.example                # Environment variable template
├── scripts/
│   └── init_db.py              # Database initialisation
├── src/
│   ├── config.py               # Settings loader (typed, validated)
│   ├── health.py               # Live health checks for all components
│   ├── db/
│   │   ├── connection.py       # psycopg v3 connection with commit/rollback
│   │   ├── schema.py           # Idempotent DDL — safe to re-run
│   │   ├── queries.py          # All DB operations (parameterised SQL)
│   │   └── chat_history.py     # Persistent conversations
│   ├── ingestion/
│   │   ├── extractor.py        # PDF, DOCX, TXT, MD extraction
│   │   ├── chunker.py          # Overlap chunking with sentence-boundary breaks
│   │   └── pipeline.py         # Full ingestion orchestration
│   ├── embeddings/
│   │   └── embedder.py         # sentence-transformers wrapper
│   ├── retrieval/
│   │   ├── vector_search.py    # pgvector cosine similarity
│   │   ├── bm25_search.py      # BM25 keyword search (normalised scores)
│   │   ├── hybrid_search.py    # RRF fusion of vector + BM25
│   │   ├── reranker.py         # Cross-encoder reranking
│   │   ├── query_rewriter.py   # LLM query rewriting
│   │   └── context_compressor.py # Sentence-level context trimming
│   ├── generation/
│   │   ├── groq_client.py      # Groq API wrapper
│   │   ├── prompts.py          # Prompt builder with citation instructions
│   │   └── citation_verifier.py # Embedding-based statement verification
│   └── evaluation/
│       ├── metrics.py          # Precision@k, Recall@k, MRR
│       └── eval_runner.py      # Evaluation pipeline
├── tests/
│   └── test_db_connection.py   # DB acceptance tests
└── deploy/
    ├── deploy.sh               # AWS Lightsail deploy script
    └── init_prod_db.sql        # Production DB initialisation
```

---

## 🔧 Technology Stack

| Component | Technology |
|---|---|
| UI | Streamlit 1.45 |
| LLM | Groq API (GPT OSS 120B / Llama 3.x) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (384d) |
| Vector database | PostgreSQL 16 + pgvector (HNSW, cosine) |
| PostgreSQL driver | psycopg v3 |
| Keyword search | rank-bm25 (BM25Okapi) |
| Reranker | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| PDF extraction | PyMuPDF |
| DOCX extraction | python-docx |
| Config | python-dotenv |
| Environment | WSL 2 (Ubuntu) |
| Deployment | Docker + Render + Neon |

---

## 📋 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key (starts with `gsk_`) |
| `GROQ_MODEL` | ✅ | Model ID e.g. `openai/gpt-oss-120b` |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `EMBEDDING_MODEL` | ❌ | Default: `all-MiniLM-L6-v2` |
| `CHUNK_SIZE` | ❌ | Default: `1000` |
| `CHUNK_OVERLAP` | ❌ | Default: `150` |
| `TOP_K` | ❌ | Default: `5` |

---

## 📊 Milestone Progress

- [x] **Milestone 1** — Foundation: skeleton, DB schema, health checks, system status page
- [x] **Milestone 2** — Core RAG: upload, chunk, embed, retrieve, generate, citations
- [x] **Milestone 3** — Advanced RAG: hybrid retrieval, reranking, query rewriting, RAG Lab
- [x] **Milestone 4** — Product: persistent chat history, evaluation dashboard, cloud deployment

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">Built with ❤️ by <strong>Hastings AI</strong></p>
