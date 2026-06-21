# GTM Agent Factory

> Phase 3 — AI SDR workflow with SQLite persistence and GTM evaluation metrics.

Inspired by monday.com RevAI. The goal is **not** another chatbot — it's an AI system that solves a GTM business problem with measurable agent outputs.

---

## Phase 3 Evaluation (Current)

**Goal:** Measure business impact from persisted agent runs.

**KPIs:**
- Total Leads
- Qualified Leads / Qualification Rate
- Average Lead Score
- Meeting Recommendation Rate

**Not included yet** (future phases):
- A/B prompt testing (Phase 4)
- LangGraph (Phase 5)
- Tool calling (Phase 6)
- Vector DB / Embeddings / RAG (Phase 7)

---

## Flow

```
Lead Input
    ↓
Qualification Agent  →  score 0-100, qualified/not, reason
    ↓
Outreach Agent       →  email, LinkedIn, discovery questions
    ↓
Recommendation Agent →  book_meeting | send_email | nurture | reject
    ↓
GTM Metrics          →  qualification rate, avg score, meeting rate
    ↓
MVP Dashboard        →  Lead, Score, Qualification, Recommendation
```

---

## Features

### 1. Lead Submission
User enters:
- Company Name
- Industry
- Company Size
- Lead Message

Example from vision doc:
```
Company: Acme
Industry: SaaS
Employees: 100
Message: "We are looking for a project management solution."
```

### 2. Qualification Agent
```json
{
  "qualified": true,
  "score": 88,
  "reason": "Strong fit for collaboration tools"
}
```

### 3. Outreach Agent
```json
{
  "email": "...",
  "linkedin": "...",
  "questions": ["...", "..."]
}
```

### 4. Recommendation Agent
```json
{
  "next_action": "book_meeting"
}
```

Possible actions: `reject`, `nurture`, `send_email`, `book_meeting`

### 5. MVP Dashboard
Displays per lead:
- Lead (company name)
- Score
- Qualification
- Recommendation

### 6. Agent Pipeline Diagram
Visual workflow card showing the 4-step agent flow, with live status (Pending → Running → Complete) and key outputs after a lead is processed.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, TypeScript, React |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | SQLite |
| AI | OpenAI API (structured JSON outputs) |

---

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Optional: add OPENAI_API_KEY (works in mock mode without it)

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open **http://localhost:3000**

---

## Project Structure

```
gtm-agent-factory/
├── project_vision.md          # Full phased roadmap
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI routes
│   │   ├── pipeline.py          # Simple sequential orchestration
│   │   ├── evaluation.py        # GTM KPI aggregation
│   │   ├── repository.py        # SQLite persistence
│   │   ├── schemas.py           # Pydantic models
│   │   ├── config.py
│   │   ├── db/                  # SQLAlchemy models + session
│   │   └── agents/
│   │       ├── qualification_agent.py
│   │       ├── outreach_agent.py
│   │       └── recommendation_agent.py
│   └── requirements.txt
└── frontend/
    ├── app/page.tsx             # MVP dashboard + GTM metrics
    └── components/
        ├── LeadForm.tsx
        ├── EvaluationMetrics.tsx
        └── LeadPipeline.tsx
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/evaluation/metrics` | GTM KPIs (qualification rate, avg score, meeting rate) |
| GET | `/api/leads/summary` | Lead count summary |
| POST | `/api/leads/submit` | Submit lead + run agents |
| GET | `/api/leads` | List all leads |
| GET | `/api/leads/{id}` | Get lead details |

---

## Mock Mode

Without `OPENAI_API_KEY`, agents return deterministic mock responses based on message keywords. Perfect for demos without API costs.

---

## Roadmap (from project_vision.md)

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | MVP workflow | ✅ |
| 2 | SQLite persistence + agent_runs | ✅ |
| 3 | Evaluation KPIs dashboard | ✅ Current |
| 4 | A/B prompt testing | 🔜 Next |
| 5 | LangGraph orchestration | 🔜 |
| 6 | Tool calling (company lookup) | 🔜 |
| 7 | RAG (product docs) | 🔜 |
| 8 | Production features (CRM, HITL) | 🔜 |

---

## License

MIT
