# GTM Agent Factory — Project Vision

> Version 3.0 — As-built (portfolio demo, Phases 1–8)
> Target State: AI-Native GTM Agent Platform
> Inspired by monday.com RevAI

---

# 1. Vision

GTM Agent Factory is an AI-native Go-To-Market platform designed to simulate the type of systems built by modern AI Revenue teams.

The goal is NOT to build another chatbot.

The goal is to build an Agentic System that can:

* Understand leads
* Retrieve business context
* Make qualification decisions
* Recommend products
* Generate outreach
* Evaluate its own decisions
* Run experiments
* Measure and report business KPIs

The project should demonstrate practical AI Product Engineering capabilities including:

* Agent Engineering
* LangGraph
* Tool Calling
* RAG
* Embeddings
* Vector Search
* Evaluation Frameworks
* Prompt Experimentation
* Business KPI measurement

**As-built note:** KPIs are computed and displayed on the evaluation dashboard; there is no closed-loop auto-optimization of prompts or actions from KPI outcomes yet.

---

# 2. Business Problem

Revenue teams spend significant time:

* Researching leads
* Understanding customer needs
* Matching products
* Writing outreach
* Prioritizing opportunities

The objective is to automate the first stages of the GTM funnel using AI Agents.

The system should behave similarly to a RevOps or Sales Development team member.

---

# 3. Current State (As-Built)

The portfolio demo implements **Phases 1–8** of the development roadmap. The system is a **7-agent LangGraph workflow** with SQLite persistence, ChromaDB RAG, observability, and human review.

**Implemented:**

✅ Planner Agent

✅ Research Agent (tools + RAG)

✅ Qualification Agent (playbook scoring, guardrails, reasoning)

✅ Product Fit Agent (catalog + case-study matching)

✅ Outreach Agent

✅ Recommendation Agent (`book_meeting` | `send_email` | `nurture` | `reject` | `human_review`)

✅ Evaluation Agent (confidence, `needs_human_review`)

✅ Shared `GTMState` (LangGraph) + `/api/leads/{id}/state`

✅ Knowledge base (`knowledge/`) + ChromaDB vector index

✅ Tool registry (`GET /api/tools`) — CRM, catalog, pricing, playbooks, case studies, RAG search

✅ SQLite persistence — leads, agent runs, experiment runs

✅ Evaluation dashboard — qualification rate, avg score, meeting rate, human-review rate

✅ Observability — per-agent prompt version, tools, docs, latency, tokens

✅ Prompt A/B — qualification v1 vs v2 (`POST /api/experiments/compare` + UI)

✅ Human review — post-pipeline approve/reject (`POST /api/leads/{id}/review`)

**Key API surface:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/leads/submit` | Run full LangGraph pipeline |
| GET | `/api/leads`, `/api/leads/{id}` | Dashboard + lead detail |
| GET | `/api/leads/{id}/state` | Shared GTMState snapshot |
| GET | `/api/leads/{id}/observability` | Per-agent runs (latency, tokens, tools) |
| GET | `/api/evaluation/metrics` | Business KPIs |
| GET | `/api/knowledge` | KB inventory + ChromaDB status |
| GET | `/api/tools` | Tool registry |
| GET/POST | `/api/experiments`, `/api/experiments/compare` | A/B prompt runs |
| POST | `/api/leads/{id}/review` | Human approve/reject |

**Current architecture:**

```text
Lead Input (Next.js)
↓
LangGraph orchestrator (backend/app/graph.py)
↓
Planner → Research → Qualification → Product Fit → Outreach → Recommendation → Evaluation
↓
SQLite (leads, agent_runs, experiment_runs)
↓
ChromaDB (chunked markdown embeddings)
↓
Dashboard + observability + experiments + HITL UI
```

**Not implemented (Phase 9):** auth, live CRM integrations, deployment, pipeline gating on human review.

---

# 4. Architecture

The target 7-agent workflow is **implemented** and orchestrated by LangGraph:

```text
Lead
↓
Planner Agent
↓
Research Agent
↓
Qualification Agent
↓
Product Fit Agent
↓
Outreach Agent
↓
Recommendation Agent
↓
Evaluation Agent
```

All agents share a common state. Guardrails (`backend/app/agents/guardrails.py`) enforce business rules separately from LLM reasoning. Partial pipeline results are persisted when a step fails.

**Stack:** FastAPI · LangGraph · SQLite · ChromaDB · OpenAI (optional mock path without API key) · Next.js

---

# 5. Shared State

All agents operate on a shared LangGraph state (`backend/app/state.py`).

```python
class GTMState(TypedDict):
    lead: dict
    planner: dict
    research: dict
    retrieved_context: list
    qualification: dict
    product_fit: dict
    outreach: dict
    recommendation: dict
    evaluation: dict
    agent_runs: list          # orchestration — appended each step
    pipeline_error: dict      # set on step failure
```

Every agent reads defined slices (`AGENT_READS`) and writes its output slice. The frontend exposes a business snapshot via `GET /api/leads/{id}/state`.

---

# 6. Agent Design Philosophy

Agents should NOT behave like deterministic rule engines.

Agents should:

* Retrieve context
* Analyze information
* Identify patterns
* Reason about tradeoffs
* Explain decisions

Rules define guardrails.

LLMs perform reasoning.

Evaluation measures outcomes.

**As-built:** `guardrails.py` validates qualification disqualifiers, product-fit confidence, recommendation actions, and evaluation review flags independently of LLM output.

---

# 7. Qualification Agent

Purpose:

Determine whether a lead should enter the sales process.

Inputs:

* Lead Information
* CRM Context
* Qualification Playbook
* Product Context
* Case Studies

Output:

```json
{
  "qualified": true,
  "score": 84,
  "signals": [
    "Strong ICP fit",
    "Pricing engagement"
  ],
  "risks": [
    "Budget unknown"
  ],
  "reasoning": "The lead closely matches our ideal customer profile."
}
```

The agent should explain WHY a lead is qualified.

**As-built:** Mock path (no API key) uses playbook scoring; LLM path uses structured JSON + guardrails for disqualifiers. Outputs include `context_inputs`, `reasoning`, `patterns`, and `tradeoffs`. Frontend shows reasoning blocks per pipeline step.

---

# 8. Product Fit Agent

Purpose:

Recommend the most appropriate product.

Inputs:

* Lead Information
* Qualification Output
* Product Documentation
* Case Studies

Output:

```json
{
  "recommended_product": "Monday CRM",
  "alternative_products": [
    "Work Management"
  ],
  "confidence": 0.91,
  "matching_requirements": [
    "Pipeline visibility",
    "Lead tracking"
  ],
  "reasoning": "The lead's requirements align strongly with CRM capabilities."
}
```

**As-built:** Scores product catalog and case studies from retrieved context; mock and LLM paths; guardrails cap confidence when fit is weak.

---

# 9. Knowledge Base

The system should use internal business knowledge rather than internet crawling.

Folder structure:

```text
knowledge/

crm_accounts/

product_catalog/

pricing/

sales_playbooks/

case_studies/
```

The Knowledge Base simulates:

* Salesforce
* HubSpot
* Product Documentation
* Internal Sales Playbooks
* Customer Success Stories

**As-built:** Five source folders indexed; `GET /api/knowledge` returns inventory, document counts, ChromaDB status, embedding model, and indexed chunk count.

---


# 10. Planner Agent

Purpose:

Determine what information is required before making decisions.

Example output:

```json
{
  "required_sources": [
    "crm_accounts",
    "product_catalog",
    "case_studies"
  ]
}
```

The Planner Agent is responsible for orchestrating information gathering.

**As-built:** Selects `required_sources` from lead message keywords; returns `prompt_version`, `context_inputs`, and `reasoning`.

---

# 11. Research Agent

Purpose:

Collect relevant business context.

Responsibilities:

* Retrieve documents
* Execute tool calls
* Populate shared state

Output:

```json
{
  "retrieved_documents": [
    "fintech_case_study",
    "monday_crm"
  ]
}
```

**As-built:** Runs tool calls per planner sources plus ChromaDB `rag_search`; deduplicates hits into `retrieved_context` shared state.

---

# 12. Evaluation Agent

Purpose:

Evaluate decision quality.

Output:

```json
{
  "confidence": 0.88,
  "needs_human_review": false,
  "missing_information": [
    "budget"
  ]
}
```

The Evaluation Agent helps measure AI quality and reliability.

**As-built:** Runs last in the graph; guardrails force `needs_human_review` on low confidence or many missing fields. KPIs on the dashboard use only fully processed leads.

---

# 13. Local RAG

Agents should retrieve information from the Knowledge Base.

Pipeline:

```text
Markdown Documents
↓
Chunking
↓
Embeddings
↓
ChromaDB
↓
Vector Search
↓
Retrieved Context
↓
Agent Reasoning
```

The retrieved context becomes part of the shared state.

**As-built:** `backend/app/rag/` — markdown chunking → embeddings → **ChromaDB** persistent store (`backend/data/chroma/`). Embeddings: OpenAI `text-embedding-3-small` when `OPENAI_API_KEY` is set; otherwise local ONNX `all-MiniLM-L6-v2`. Re-indexes when knowledge files or embedding model change.

---

# 14. Tool Calling

Agents should be able to use tools.

Examples:

```python
search_crm_account()

search_product_catalog()

search_case_studies()

search_pricing()

search_knowledge_base()
```

Tools retrieve information.

Agents decide when and how to use them.

**As-built:** `backend/app/tools/registry.py` — `search_crm_account`, `search_product_catalog`, `search_pricing`, `search_sales_playbooks`, `search_case_studies`, `search_knowledge_base`. Research agent invokes tools; RAG is also called directly for vector retrieval.

---


# 15. Prompt Experimentation Platform

A core project goal is experimentation.

Every agent should support prompt versioning.

Example:

```text
Qualification Agent

Version A
Version B
```

Both prompts run on the same lead.

Results are stored and compared.

**As-built:** Prompt registry (`backend/app/prompts/registry.py`) holds v1/v2 for planner and qualification; v1 for research and evaluation. **A/B compare is implemented for the Qualification agent only** (`POST /api/experiments/compare`, `GET /api/experiments`, frontend Experiment panel). Other agents log `prompt_version` in observability but are not yet in the experiment runner.

---

# 16. A/B Testing Metrics

Track:

* Qualification Rate
* Meeting Recommendation Rate
* Average Lead Score
* Confidence Score
* Latency
* Token Usage

Determine winning prompt versions.

**As-built:** Dashboard KPIs track qualification rate, meeting recommendation rate, average score, confidence, and human-review rate across leads. Per-agent **latency** and **token usage** are stored in `agent_runs` and shown in the observability panel. Experiment records currently compare **qualification score and qualified/not** between prompt variants — not yet full cross-metric A/B on meeting rate or tokens.

---

# 17. Persistence

Store:

* Leads
* Agent Runs
* Retrieved Documents
* Evaluation Results
* Prompt Versions
* Experiment Runs

The database becomes the foundation for evaluation and experimentation.

**As-built:** SQLite at `backend/data/gtm.db` — tables `leads`, `agent_runs` (with prompt_version, tools_used, retrieved_documents, latency_ms, token_usage), `experiment_runs`. Prompt versions live in code registry, not a separate DB table.

---

# 18. Observability

Track:

* Agent Name
* Prompt Version
* Tools Used
* Retrieved Documents
* Confidence
* Latency
* Token Usage

Provide visibility into agent behavior.

**As-built:** Graph instrumentation records each step; `GET /api/leads/{id}/observability` and frontend Observability panel (auto-load on lead select). Token usage from OpenAI `usage` when keyed; mock estimate otherwise.

---

# 19. Human In The Loop

Agents may escalate uncertain decisions.

Possible recommendation:

```json
{
  "next_action": "human_review"
}
```

Human review should be available before production actions are executed.

**As-built (partial):** Recommendation agent and guardrails can output `next_action: "human_review"`. Evaluation sets `needs_human_review`. UI shows a Review badge and approve/reject flow. **The LangGraph pipeline does not pause before outreach/recommendation** — review is post-hoc on completed runs. Production gating (block outreach until approved) is Phase 9.

---

# 20. Development Roadmap

Phase 1

✅ Basic Agent Pipeline

Phase 2

✅ Persistence Layer

Phase 3

✅ Evaluation Dashboard

Phase 4

✅ Prompt Experimentation & A/B Testing *(qualification agent; UI + API)*

Phase 5

✅ LangGraph Migration

Phase 6

✅ Knowledge Base + Local RAG (ChromaDB + embeddings)

Phase 7

✅ Tool Calling + Research Agent

Phase 8

✅ Observability + Human Review *(observability complete; HITL post-hoc, not pipeline-gated)*

Phase 9

🔜 Production Readiness — auth, live CRM integrations, deployment, HITL gating before outreach

**Status (June 2026):** Phases 1–8 complete for portfolio demo. Phase 9 deferred.

---

# 21. Final Goal

Build a production-style AI GTM platform that demonstrates:

| Capability | Status |
|------------|--------|
| Agent Engineering | ✅ 7 agents, guardrails, reasoning, partial recovery |
| LangGraph Workflows | ✅ Sole orchestrator |
| Tool Calling | ✅ Registry + research integration |
| RAG | ✅ ChromaDB retrieval into shared state |
| Embeddings | ✅ OpenAI or local ONNX |
| Vector Databases | ✅ ChromaDB persistent index |
| Evaluation | ✅ Agent + KPI dashboard |
| Experimentation | ✅ Qualification A/B (narrow scope) |
| Business Impact | ✅ Qualification rate, scores, meeting rate, review rate |

**Portfolio demo:** **Final Goal achieved** — the system demonstrates the architecture and product-thinking behind modern AI Revenue organizations such as monday.com's RevAI.

**Production product:** **Not yet** — Phase 9 (auth, CRM, deploy, pre-outreach HITL gating, multi-agent A/B, KPI-driven prompt optimization) remains out of scope for the current build.
