# RepoMind: Autonomous Local Repository Investigation Agent

> An autonomous, read-only software repository investigation agent built with **LangGraph**, **Google Gemini**, **ChromaDB**, **FastAPI**, and **Next.js**.

---

## 1. Overview

RepoMind investigates local software repositories to answer architectural, flow-tracing, error-origin, and symbol-definition questions with verifiable line citations.

### Core Principles
1. **Local and Read-Only by Construction**: Operates strictly inside target repository directories. No file writes, branch changes, or code execution are permitted.
2. **Snapshot Identity is Immutable**: Each investigation is pinned to a commit SHA (`git rev-parse HEAD`) or directory content hash.
3. **The Index is an Accelerator; the Snapshot is Truth**: Vector chunks and AST indices accelerate lookup, but every factual claim in the final answer is verified against real file lines on disk.
4. **Policy Gateway & Sandbox Confinement**: All tool proposals pass through a security gateway enforcing path traversal prevention (`../../`), tool allowlists, and step budgets.
5. **Prompt Injection Defense & Secret Redaction**: Repository data is encapsulated in explicit system demarcation frames (`<<<UNTRUSTED_REPOSITORY_DATA>>>`) and credentials (`AKIA...`, private keys, passwords) are automatically redacted.

---

## 2. System Architecture

```mermaid
flowchart TD
    START([User Query & Repo Path]) --> Intake[intake_node]
    Intake --> Classify[classify_node]
    
    Classify --> ConditionClarify{Ambiguous?}
    ConditionClarify -- "Yes" --> Clarify[clarify_node\n*LangGraph interrupt()*]
    Clarify --> Plan[plan_node]
    ConditionClarify -- "No" --> Plan
    
    Plan --> SelectAction[select_action_node]
    SelectAction --> PolicyCheck[policy_check_node]
    
    PolicyCheck -- "Approved" --> ExecuteTool[execute_tool_node]
    PolicyCheck -- "Denied" --> Observe[observe_node]
    ExecuteTool --> Observe
    
    Observe --> Evaluate[evaluate_node]
    
    Evaluate -- "Tool failed" --> Reflect[reflect_node] --> SelectAction
    Evaluate -- "Need more evidence" --> SelectAction
    Evaluate -- "Need replan" --> Plan
    Evaluate -- "Contradiction detected" --> Reconcile[reconcile_node] --> SelectAction
    Evaluate -- "Sufficient OR Budget Reached" --> Synthesize[synthesize_node]
    
    Synthesize --> Verify[verify_node]
    Verify -- "Missing line proof" --> SelectAction
    Verify -- "Verified" --> Answer[answer_node] --> END([Final Answer + Citations])
```

---

## 3. Technology Stack

- **Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph) (`StateGraph` with conditional routing, `MemorySaver` checkpointer, and `interrupt()`)
- **LLM Engine**: Google Gemini via `langchain-google-genai`
- **Knowledge Plane**:
  - Python AST Symbol Indexer (`ast` module)
  - ChromaDB + FastEmbed (`BAAI/bge-small-en-v1.5`)
  - Lexical / Regex code search & directory snapshot hashing
  - Regex secret scanner & redaction
- **Backend API**: FastAPI, Uvicorn, and Server-Sent Events (SSE) via `sse-starlette`
- **Frontend UI**: Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide icons

---

## 4. Quickstart Guide

### Prerequisites
- Python 3.11+ and `uv` package manager
- Node.js 18+ and `pnpm` (or `npm`)
- Google Gemini API Key (`GOOGLE_API_KEY`)

### Setup Environment

```bash
# 1. Clone repository
git clone https://github.com/your-username/agentic-ai-project.git
cd agentic-ai-project

# 2. Configure environment
cp .env.example .env
# Edit .env and supply your GOOGLE_API_KEY

# 3. Install Python dependencies
uv sync --all-extras

# 4. Install Frontend dependencies
cd frontend && pnpm install && cd ..
```

### Running the Full-Stack Application

In two separate terminals:

```bash
# Terminal 1: Launch FastAPI Backend (Port 8000)
make dev-backend
# Alternatively: uv run uvicorn backend.main:app --reload --port 8000

# Terminal 2: Launch Next.js UI (Port 3000)
make dev-frontend
# Alternatively: cd frontend && pnpm run dev
```

Open your browser at **`http://localhost:3000`** to access the RepoMind dashboard.

---

## 5. Running Tests & Benchmarks

```bash
# Run all unit tests (routing, tools, policy gateway)
uv run --extra dev pytest tests/unit/ -v

# Run backend API integration tests
uv run --extra dev pytest tests/integration/test_api.py -v

# Run the complete automated evaluation suite (6 benchmark scenarios)
uv run python backend/evaluation/harness.py
```

---

## 6. API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check endpoint returning backend status and version. |
| `POST` | `/api/investigate` | Start a new investigation `{ repo_path, query, max_steps }`. Returns `investigation_id`. |
| `GET` | `/api/investigate/stream/{id}` | Real-time SSE stream emitting `node_change`, `plan_update`, `tool_call`, `tool_result`, `reflection`, `token`, `interrupt`, and `done`. |
| `POST` | `/api/investigate/resume/{id}` | Resumes a paused investigation with user clarifying guidance `{ response }`. |
| `GET` | `/api/investigate/{id}/state` | Fetches the full current state snapshot, plan, findings, and evidence. |

---

## 7. Project Structure

```
agentic-ai-project/
├── backend/
│   ├── main.py                  # FastAPI application entrypoint & CORS config
│   ├── config.py                # Shared settings and environment defaults
│   ├── api/
│   │   ├── models.py            # Pydantic schemas for requests/responses
│   │   ├── manager.py           # Investigation session lifecycle & SSE pub/sub
│   │   └── routes.py            # API endpoint handlers
│   ├── agent/
│   │   ├── state.py             # InvestigationState TypedDict with reducers
│   │   ├── llm.py               # Google Gemini factory
│   │   ├── graph.py             # LangGraph StateGraph builder & routers
│   │   └── nodes/               # 14 LangGraph node handlers
│   ├── knowledge/               # AST engine, ChromaDB vector store, secret scanner
│   ├── policy/                  # PolicyGateway sandbox & untrusted framing
│   ├── tools/                   # 10 local read-only repository tools
│   └── evaluation/              # Benchmark harness and scenario runner
├── frontend/                    # Next.js / React user interface
│   ├── src/app/                 # App Router pages and global styles
│   ├── src/components/          # UI components (Plan, Feed, Evidence, Answer)
│   └── src/types/               # TypeScript data definitions
├── tests/
│   ├── fixtures/sample_repo/    # Reference repository for test suites
│   ├── unit/                    # 30 unit tests (tools, policy, routing)
│   ├── integration/             # 10 API and agent integration tests
│   └── evaluation/scenarios/    # 5 adversarial evaluation scenarios
├── EVALUATION_REPORT.md         # Full benchmark and adversarial capstone report
└── ARCHITECTURE.md              # Complete technical architecture specification
```

