# GTM Agent Factory

> Phase 1 MVP — AI SDR workflow that automates lead qualification, outreach, and recommendation.

Inspired by monday.com RevAI. The goal is **not** another chatbot — it's an AI system that solves a GTM business problem with measurable agent outputs.

---

## Phase 1 MVP (Current)

**Goal:** Build a complete workflow as quickly as possible. Keep it simple.

**Not included yet** (future phases):
- LangGraph (Phase 5)
- Vector DB / Embeddings / RAG (Phase 7)
- SQLite persistence (Phase 2)
- A/B prompt testing (Phase 4)
- Tool calling (Phase 6)

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
| Backend | Python, FastAPI, Pydantic |
| AI | OpenAI API (structured JSON outputs) |
| Storage | In-memory (Phase 1 only) |

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
│   │   ├── store.py             # In-memory lead store
│   │   ├── schemas.py           # Pydantic models
│   │   ├── config.py
│   │   └── agents/
│   │       ├── qualification_agent.py
│   │       ├── outreach_agent.py
│   │       └── recommendation_agent.py
│   └── requirements.txt
└── frontend/
    ├── app/page.tsx             # MVP dashboard
    └── components/
        ├── LeadForm.tsx
        └── LeadPipeline.tsx
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
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
| 1 | MVP workflow | ✅ Current |
| 2 | SQLite persistence + agent_runs | 🔜 Next |
| 3 | Evaluation KPIs dashboard | 🔜 |
| 4 | A/B prompt testing | 🔜 |
| 5 | LangGraph orchestration | 🔜 |
| 6 | Tool calling (company lookup) | 🔜 |
| 7 | RAG (product docs) | 🔜 |
| 8 | Production features (CRM, HITL) | 🔜 |

---

## License

MIT
