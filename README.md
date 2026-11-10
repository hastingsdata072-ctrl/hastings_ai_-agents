# AI Agents & Intelligence Portfolio

Five production-style AI and ML projects spanning Amazon Bedrock AgentCore, multi-agent orchestration, RAG, and document intelligence. Each project is self-contained with its own README, architecture diagram, source code, infrastructure, and test evidence.

---

## Projects

### 1. [Customer Support Chatbot](./customer-support-chatbot/)
A prompt-engineered chatbot that handles customer support scenarios end-to-end — filing bug tickets, answering FAQ questions, and routing out-of-scope requests to human agents. All routing and grounding logic lives in a single system prompt.

**Stack:** Amazon Bedrock AgentCore · Amazon Nova Pro · AWS Lambda · DynamoDB · Bedrock Evaluations

---

### 2. [AI Support Agent](./ai-support-agent/)
A fully deployed AI support agent with order tracking, refund processing, loyalty discount calculation, live web browsing, and cross-session memory. Built with the Strands Agents framework on top of AgentCore.

**Stack:** Amazon Bedrock AgentCore · Strands Agents · Amazon Nova 2 Lite · AWS Lambda · Bedrock Knowledge Base · AgentCore Memory · Code Interpreter · AgentCore Browser

---

### 3. [NovaMart Multi-Agent Support System](./novamart-multi-agent-support/)
A production-grade multi-agent system that routes customer requests through a 5-agent hierarchy — inventory lookup, parallel multi-agent RAG across 3 knowledge bases, refund eligibility decisions, and response composition. Fully deployed on AgentCore Runtime with Bedrock Guardrails, AgentCore Memory, and end-to-end X-Ray observability. **120/120 on the automated test suite.**

**Stack:** Strands Agents · Amazon Bedrock AgentCore · Claude Haiku 4.5 + Sonnet 4.5 · DynamoDB · Bedrock Knowledge Bases × 3 · Bedrock Guardrails · AgentCore Memory · AWS X-Ray · CloudWatch

---

### 4. [Hastings RAG Studio](./hastings-rag-studio/)
A professional Document Intelligence and Agentic RAG platform. Upload documents, ask questions, and receive evidence-grounded answers with full citations. Features a full advanced RAG pipeline: hybrid vector + BM25 retrieval with RRF fusion, cross-encoder reranking, query rewriting, context compression, citation verification, persistent chat history, and an evaluation dashboard.

**Stack:** Python 3.11 · Streamlit · Groq API (GPT OSS 120B / Llama 3.x) · PostgreSQL + pgvector (HNSW) · sentence-transformers · rank-bm25 · Docker · Render + Neon · WSL 2 (Ubuntu)

---

### 5. [Linda Afya Health Assistant](./linda-afya/)
A bilingual (English/Kiswahili) AI health assistant aligned with Kenya Ministry of Health guidelines. Provides symptom triage (RED/YELLOW/GREEN decision matrix), clinic location across 13,000+ MoH facilities, immunization tracking against the Kenya KEPI schedule, and free-form AI health chat grounded in official MoH clinical documents.

**Stack:** Streamlit · OpenRouter · NVIDIA Nemotron 3 Ultra 550B · pandas · Streamlit Community Cloud · Future: Amazon Bedrock AgentCore + Bedrock Knowledge Bases

---

## AWS services used across projects

| Service | Used in |
|---|---|
| Amazon Bedrock AgentCore (managed harness / runtime) | Projects 1, 2, 3 |
| Amazon Nova Pro / Nova 2 Lite | Projects 1, 2 |
| Claude Haiku 4.5 / Sonnet 4.5 | Project 3 |
| AgentCore Gateway (MCP) | Projects 1, 2 |
| AWS Lambda | Projects 1, 2 |
| Amazon DynamoDB | Projects 1, 3 |
| Amazon Bedrock Knowledge Base | Projects 2, 3 |
| AgentCore Memory | Projects 2, 3 |
| AgentCore Code Interpreter | Project 2 |
| AgentCore Browser | Project 2 |
| Amazon Bedrock Guardrails | Project 3 |
| AWS X-Ray | Project 3 |
| Amazon CloudWatch Logs | Project 3 |
| Amazon Bedrock Evaluations | Project 1 |
| AWS CloudFormation | Projects 1, 2, 3 |

---

## Tech stack — Projects 4 & 5

| Component | Hastings RAG Studio (Project 4) | Linda Afya (Project 5) |
|---|---|---|
| Language | Python 3.11 | Python 3.11 |
| UI framework | Streamlit 1.45 | Streamlit 1.45 |
| LLM / AI API | Groq API (GPT OSS 120B · Llama 3.3 70B · Llama 3.1 8B) | OpenRouter (NVIDIA Nemotron 3 Ultra 550B) |
| Vector database | PostgreSQL 16 + pgvector (HNSW index, cosine similarity) | — |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (384d) | — |
| Keyword search | rank-bm25 (BM25Okapi) | — |
| Reranker | cross-encoder/ms-marco-MiniLM-L-6-v2 | — |
| DB driver | psycopg v3 + psycopg-pool | — |
| Data handling | — | pandas |
| Maps | — | folium |
| PDF extraction | PyMuPDF | — |
| DOCX extraction | python-docx | — |
| Config | python-dotenv | python-dotenv |
| Containerisation | Docker (multi-stage build) | — |
| Deployment | Render (free tier) + Neon (serverless pgvector) | Streamlit Community Cloud |
| Dev environment | WSL 2 (Ubuntu) | WSL 2 (Ubuntu) |

---

## Security note

AWS credentials, API keys, and sensitive resource identifiers are kept out of source control. Each project includes a `.gitignore` that excludes `.env` files and generated artifacts. Configuration values are loaded from environment variables at runtime. See each project's `.env.example` for the required keys.
