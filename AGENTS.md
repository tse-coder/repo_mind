# AGENTS.md — RepoMind Project Context & Instructions

> **Notice for Agents:** This repository contains **RepoMind**, an autonomous, read-only repository investigation agent built with **LangGraph**, **Google Gemini**, **ChromaDB**, and a **FastAPI + Next.js** stack. Read this file to understand the project status, environment conventions, architecture rules, and remaining implementation phases.

---

## 1. Project Overview & Core Principles

RepoMind investigates local software repositories to answer architectural, flow-tracing, error-origin, and symbol-definition questions with verifiable line citations.

### Guiding Principles:
1. **Local and Read-Only by Construction:** Tools operate strictly inside the target repository. No code execution, git writes, or file mutations are permitted.
2. **Snapshot Identity is Immutable:** Each investigation is pinned to a commit SHA (`git rev-parse HEAD`) or directory content hash.
3. **The Index is an Accelerator; the Snapshot is the Truth:** Vector search chunks guide the agent, but every factual assertion in the final answer must be verified against actual lines read from the source file.
4. **The Model Proposes; the Application Disposes:** All tool calls pass through the `PolicyGateway` (validates path sandboxing, allowlists, and step budgets).
5. **Prompt Injection Defense:** Repository files are treated strictly as data. Tool outputs are encapsulated in `<<<UNTRUSTED_REPOSITORY_DATA>>>` frames, and credentials are automatically redacted.

---

## 2. Environment & Commands

- **Package Manager:** `uv` with Python 3.13 in local `.venv` (managed by `uv.lock`).
- **Never use global pip.** Always run commands via `uv run` or `uv run --extra dev`.
- **LLM Configuration:** `.env` contains `GOOGLE_API_KEY` (using Google's current `gemini-3.8-flash` model).

### Key Commands:
```bash
# Run all 30 unit tests (takes ~4s)
uv run --extra dev pytest tests/unit/ -v

# Run linting
uv run ruff check backend/ tests/

# Execute the LangGraph investigation agent on a local repo
uv run python -c "
from backend.agent.graph import create_investigation_app
app = create_investigation_app()
inputs = {
    'repo_path': 'tests/fixtures/sample_repo',
    'query': 'Where is the login handler defined?',
    'max_steps': 3,
    'tool_history': [],
    'evidence_store': [],
    'findings': [],
    'reflections': [],
}
for event in app.stream(inputs, config={'configurable': {'thread_id': 's1'}}):
    print(event)
"
```

---

## 3. Current Implementation Status

| Phase | Description | Status | Verification |
|---|---|---|---|
| **Phase 0** | Scaffold, `uv` environment, `.venv`, `pyproject.toml`, `Makefile` | ✅ Complete | Clean imports & venv |
| **Phase 1** | `InvestigationState` schema, 14 LangGraph nodes, `StateGraph`, `MemorySaver` | ✅ Complete | Graph compiles & routes conditionally |
| **Phase 2** | Knowledge Plane: AST engine, ChromaDB vector store, secret scanner, 10 tools | ✅ Complete | 13/13 unit tests passed |
| **Phase 3** | Policy Gateway (path sandboxing, allowlist, secret redaction, framing) | ✅ Complete | 6/6 policy tests passed |
| **Phase 4** | Gemini LLM integration, structured Pydantic schemas, fast observe extraction | ✅ Complete | 30/30 unit tests passed |
| **Phase 5** | FastAPI Backend & SSE streaming endpoints | ⏳ **Next to build** | — |
| **Phase 6** | Next.js / React User Interface | ⏳ Pending | — |
| **Phase 7** | Evaluation Harness, 5 Adversarial Scenarios, Capstone Report | ⏳ Pending | — |

---

## 4. Codebase Directory Map

```
agentic-ai-project/
├── backend/
│   ├── config.py                  # Environment settings, defaults (DEFAULT_MAX_STEPS=5)
│   ├── agent/
│   │   ├── state.py               # InvestigationState TypedDict with append-only reducers
│   │   ├── llm.py                 # Google Gemini factory (ChatGoogleGenerativeAI)
│   │   ├── graph.py               # StateGraph wiring, conditional edge routers, MemorySaver
│   │   └── nodes/                 # 14 LangGraph node handlers:
│   │       ├── intake.py          # Resolves Git SHA & sets initial state
│   │       ├── classify.py        # LLM question classification (LOCATE, TRACE_FLOW, etc.)
│   │       ├── clarify.py         # Human-in-the-loop pause via interrupt()
│   │       ├── plan.py            # LLM sub-goal planning
│   │       ├── select_action.py   # LLM tool selection with 1-sentence rationale
│   │       ├── policy_check.py    # PolicyGateway interception
│   │       ├── execute_tool.py    # Dispatches tool and frames output
│   │       ├── observe.py         # Fast deterministic extraction of EvidenceItem & Finding
│   │       ├── evaluate.py        # 8-way conditional router (budgets, retries, sufficiency)
│   │       ├── reflect.py         # Reflexion self-critique on failures
│   │       ├── reconcile.py       # Code > config > tests > docs authority resolution
│   │       ├── synthesize.py      # Draft answer with inline [file:line] citations
│   │       ├── verify.py          # Programmatic on-disk citation verification
│   │       └── answer.py          # Formats final output with confidence labels
│   ├── tools/                     # 10 execution tools + registry:
│   │   ├── __init__.py            # dispatch_tool(repo_path, tool_slug, args)
│   │   ├── explore_tree.py        # Directory listing with depth/glob filters
│   │   ├── read_file.py           # Ground truth file lines + content hashes
│   │   ├── search_code.py         # Lexical & regex code search
│   │   ├── search_symbols.py      # AST symbol search
│   │   ├── get_symbol.py          # Full symbol definition extraction
│   │   ├── find_references.py     # Usages and invocations of symbols
│   │   ├── get_relationships.py   # Imports & imported-by dependency graph
│   │   ├── trace_calls.py         # Recursive static call tree
│   │   ├── semantic_search.py     # ChromaDB + FastEmbed concept search
│   │   └── get_history.py         # Git log & blame reader
│   ├── knowledge/                 # Knowledge plane engines:
│   │   ├── snapshot.py            # Resolves Git SHA or dir hash
│   │   ├── ast_parser.py          # Python AST visitor and RepoASTIndex
│   │   ├── vector_store.py        # ChromaDB client & text chunking
│   │   └── secret_scanner.py      # Credential detection & redaction regexes
│   └── policy/                    # Security layer:
│       ├── gateway.py             # Sandbox path confinement & budget limits
│       └── framing.py             # <<<UNTRUSTED_REPOSITORY_DATA>>> wrapper
├── tests/
│   ├── fixtures/sample_repo/      # Multi-file sample project used by test suites
│   ├── unit/                      # 30 unit tests (routing, tools, policy)
│   └── integration/               # End-to-end graph tests
├── ARCHITECTURE.md                # Full architecture specification
├── IMPLEMENTATION_PLAN.md         # 8-phase implementation roadmap
└── pyproject.toml / Makefile      # Project configuration
```

---

## 5. Next Steps for Incoming Agent (Phase 5 & Beyond)

### Phase 5 — FastAPI Backend & SSE Streaming:
1. Implement `backend/main.py`:
   - Initialize FastAPI with CORS allowing `http://localhost:3000`.
   - Health check endpoint: `GET /api/health`.
2. Implement `backend/api/routes.py`:
   - `POST /api/investigate`: Receives `{ repo_path: str, query: str }`, generates an `investigation_id`, and initiates the graph run.
   - `GET /api/investigate/stream/{id}`: Streams Server-Sent Events (SSE) using `sse-starlette` consuming `graph.astream_events(..., version="v2")`. Emits events for: `node_start`, `tool_call`, `tool_result`, `plan_update`, `reflection`, `token`, `answer`, `done`.
   - `POST /api/investigate/resume/{id}`: Delivers user feedback to resume interrupted runs (`Command(resume=...)`).
3. Add integration test `tests/integration/test_api.py` using `httpx.AsyncClient` or FastAPI `TestClient`.

### Phase 6 — Next.js Frontend:
- Build the dashboard in `frontend/`:
  - Local repository directory selector.
  - Live plan checklist (updates dynamically as sub-goals change).
  - Tool activity feed with accordion collapsible args and framed results.
  - Interactive evidence panel highlighting cited code and line ranges.
  - Clarification popup dialog for `interrupt()` events.

### Phase 7 — Capstone Deliverables (Slides 22 & 23):
- Build 5 adversarial test scenarios in `tests/evaluation/scenarios/` (prompt injection test, contradiction test, missing parameter test, tool timeout test, and empty repo test).
- Generate event logs demonstrating agentic behavior (plan revision, reflection on tool failure, state updates).
- Write `EVALUATION_REPORT.md` (1-page evaluation report) and `README.md`.
