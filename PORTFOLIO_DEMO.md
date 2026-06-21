# Portfolio Demo — GTM Agent Factory

A 5-minute walkthrough for reviewers and hiring managers.

## Start the stack

```bash
# Terminal 1 — backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

Open http://localhost:3000

Optional: set `OPENAI_API_KEY` in `backend/.env` for real LLM reasoning. Without it, agents use deterministic mocks (still fully demo-able).

---

## Demo script

### 1. Submit a lead (30s)

Use the sample from the vision doc:

- **Company:** Acme
- **Industry:** SaaS
- **Size:** 100
- **Message:** "We are looking for a project management solution."

Watch the 7-step pipeline animate: Planner → Research → Qualification → Product Fit → Outreach → Recommendation → Evaluation.

### 2. Inspect agent reasoning (1 min)

Select the lead in the dashboard. Expand pipeline steps to see:

- **Reasoning** — why the agent decided what it did
- **Context inputs** — which knowledge sources informed the step
- **Patterns / tradeoffs** — structured decision artifacts

### 3. Knowledge base (30s)

Scroll to **Knowledge Base** — shows playbook, product catalog, and case studies indexed for RAG retrieval.

### 4. Evaluation metrics (30s)

Top dashboard KPIs: qualification rate, average score, meeting recommendation rate, human-review rate — computed from persisted SQLite runs.

### 5. Prompt A/B experiment (1 min)

In **Lead Details → Prompt A/B — Qualification**, click **Run v1 vs v2**.

Side-by-side comparison of two qualification prompt versions on the same lead — winner by score, without re-running the full pipeline.

### 6. Observability (1 min)

**Agent Observability** table loads automatically per lead:

| Column | Meaning |
|--------|---------|
| Prompt | Registered prompt version |
| Tools | Tools invoked (research step) |
| Docs | RAG documents retrieved |
| Latency | Per-agent ms |
| Tokens | LLM usage (or mock estimate) |

### 7. Human review (30s)

If evaluation flags `needs_human_review`, a **Review** badge appears in the dashboard. Approve or reject with optional notes — persisted on the lead.

---

## Architecture highlights (talking points)

- **LangGraph** orchestrates 7 agents with shared `GTMState`
- **Guardrails** separate from LLM reasoning (disqualifiers, confidence thresholds)
- **SQLite persistence** — leads, agent runs, experiments survive refresh
- **ChromaDB + embeddings** — markdown → chunk → embed → vector search (OpenAI or local ONNX)
- **Experimentation API** — `POST /api/experiments/compare`, `GET /api/experiments`

---

## API smoke test

```bash
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8000/api/knowledge | jq '.total_documents'
curl -s http://localhost:8000/api/evaluation/metrics | jq
```

---

## Tests

```bash
cd backend && pytest -q
```

50 tests cover agents, guardrails, persistence, RAG, and partial pipeline recovery.
