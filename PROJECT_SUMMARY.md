# GTM Agent Factory — מסמך מסכם

> עדכון: 19 ביוני 2026  
> שלב נוכחי: **Phase 3 — Evaluation Layer**

---

## 1. חזון הפרויקט

**GTM Agent Factory** הוא פלטפורמת Go-To-Market מבוססת AI, בהשראת צוות RevAI של monday.com.

המטרה אינה לבנות צ'אטבוט, אלא מערכת סוכנים (agents) שמבצעת את שלבי ה-GTM הראשונים:

- סינון והכשרת לידים (Lead Qualification)
- יצירת תוכן outreach מותאם אישית
- המלצה על פעולה הבאה (book meeting / send email / nurture / reject)
- מדידת KPIs עסקיים

הפרויקט מדגים יכולות AI Product Engineering: Agent Engineering, LangGraph (בעתיד), Tool Calling, RAG, Evaluation Frameworks ועוד.

---

## 2. מה נבנה עד כה — סיכום שלבים

| שלב | תיאור | סטטוס |
|-----|--------|--------|
| **Phase 1** | MVP — workflow בסיסי עם 3 סוכנים | ✅ הושלם |
| **Phase 2** | שמירה ב-SQLite + טבלת `agent_runs` | ✅ הושלם |
| **Phase 3** | שכבת Evaluation — KPIs ודשבורד | ✅ **שלב נוכחי** |
| Phase 4 | A/B testing לפרומפטים | 🔜 הבא |
| Phase 5 | LangGraph orchestration | 🔜 |
| Phase 6 | Tool calling (חיפוש חברות) | 🔜 |
| Phase 7 | RAG (מסמכי מוצר) | 🔜 |
| Phase 8 | Production (CRM, HITL) | 🔜 |

---

## 3. ארכיטקטורה

```
Lead Input (Frontend)
       ↓
Qualification Agent  →  score 0-100, qualified/not, reason
       ↓
Outreach Agent       →  email, LinkedIn, discovery questions
       ↓
Recommendation Agent →  book_meeting | send_email | nurture | reject
       ↓
SQLite Persistence   →  leads + agent_runs
       ↓
GTM Metrics          →  qualification rate, avg score, meeting rate
       ↓
MVP Dashboard        →  Lead, Score, Qualification, Recommendation
```

### Tech Stack

| שכבה | טכנולוגיה |
|------|-----------|
| Frontend | Next.js, TypeScript, React |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | SQLite (`backend/data/gtm.db`) |
| AI | OpenAI API (structured JSON outputs) |

---

## 4. Backend — מה קיים

### 4.1 API Endpoints

| Method | Endpoint | תיאור |
|--------|----------|--------|
| GET | `/health` | בדיקת תקינות + מספר לידים |
| GET | `/api/evaluation/metrics` | KPIs עסקיים |
| GET | `/api/leads/summary` | סיכום מספר לידים |
| POST | `/api/leads/submit` | שליחת ליד + הרצת pipeline |
| GET | `/api/leads` | רשימת כל הלידים |
| GET | `/api/leads/{id}` | פרטי ליד בודד |

### 4.2 Pipeline (`pipeline.py`)

אורקסטרציה **סדרתית פשוטה** (ללא LangGraph):

1. **Input validation** — בדיקת שם חברה והודעה
2. **Qualification Agent**
3. **Outreach Agent**
4. **Recommendation Agent**

כל שלב נשמר ב-`agent_runs` עם input/output JSON. יש delay של 2 שניות בין שלבים (להדגמה ויזואלית).

### 4.3 שלושת הסוכנים

#### Qualification Agent
- **קלט:** company_name, industry, company_size, message
- **פלט:** `qualified` (boolean), `score` (0-100), `reason`
- **סף:** score ≥ 60 = qualified
- **Mock mode:** ניקוד לפי מילות מפתח (demo, pricing, urgent וכו')

#### Outreach Agent
- **קלט:** נתוני ליד + תוצאות qualification
- **פלט:** `email`, `linkedin`, `questions` (4 שאלות discovery)
- **Mock mode:** תבנית קבועה עם שם החברה והתעשייה

#### Recommendation Agent
- **קלט:** נתוני ליד + qualification + outreach
- **פלט:** `next_action` — אחד מ: `book_meeting`, `send_email`, `nurture`, `reject`
- **סף:** score ≥ 75 → book_meeting

### 4.4 מסד נתונים

**טבלת `leads`:**
- id, company_name, industry, company_size, message, created_at

**טבלת `agent_runs`:**
- id, lead_id, agent_name, input (JSON), output (JSON), created_at

### 4.5 Evaluation Layer (`evaluation.py`)

KPIs שמחושבים מהנתונים השמורים:

| KPI | תיאור |
|-----|--------|
| `total_leads` | סך כל הלידים |
| `qualified_leads` | לידים שעברו qualification |
| `qualification_rate` | qualified / total |
| `meeting_recommendations` | לידים עם next_action = book_meeting |
| `meeting_recommendation_rate` | meeting / total |
| `average_score` | ממוצע score (רק לידים עם qualification run) |
| `processed_leads` | לידים שהשלימו את כל 3 הסוכנים |

### 4.6 Mock Mode

ללא `OPENAI_API_KEY` — הסוכנים מחזירים תשובות דטרמיניסטיות. מתאים לדמו ללא עלות API.

**הגדרות** (`.env`):
```
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
CORS_ORIGINS=http://localhost:3000
STEP_DELAY_SEC=2.0
DATABASE_URL=sqlite:///./data/gtm.db
```

### 4.7 בדיקות

`backend/tests/test_evaluation.py` — 5 טests ל-metrics:
- DB ריק
- qualification rates מעורבים
- meeting recommendation rate
- pipeline חלקי (רק qualification)
- סינון לפי lead_ids

---

## 5. Frontend — מה קיים

### 5.1 דף ראשי (`app/page.tsx`)

ארבעה אזורים:

1. **Submit Lead** — טופס הזנת ליד + לידים לדוגמה (Acme, GreenEnergy)
2. **Agent Pipeline** — דיאגרמה ויזואלית עם סטטוס (Pending → Running → Complete)
3. **GTM Evaluation Metrics** — פאנל KPIs
4. **MVP Dashboard** — טבלה: Lead | Score | Qualification | Recommendation
5. **Lead Details** — פירוט מלא של הליד הנבחר (outreach, questions וכו')

### 5.2 קומפוננטות

| קומפוננטה | תפקיד |
|-----------|--------|
| `LeadForm.tsx` | טופס שליחה + לידים לדוגמה |
| `PipelineDiagram.tsx` | דיאגרמת workflow עם סטטוס חי |
| `EvaluationMetrics.tsx` | תצוגת KPIs |
| `LeadPipeline.tsx` | פירוט תוצאות סוכנים |
| `Card.tsx` | wrapper לכרטיסים |
| `PersistedStatus.tsx` | אינדיקציה לשמירה ב-DB |

### 5.3 API Client (`lib/api.ts`)

- חיבור ל-backend ב-`http://localhost:8000`
- טיפול בשגיאות pipeline (failed_step)
- `PIPELINE_STEP_MS = 2000` — מסונכרן עם backend

---

## 6. מבנה תיקיות

```
agentFactory/
├── project_vision.md          # חזון ו-roadmap
├── README.md                  # תיעוד Phase 3
├── PROJECT_SUMMARY.md         # מסמך זה
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI routes
│   │   ├── pipeline.py          # orchestration
│   │   ├── evaluation.py        # KPI aggregation
│   │   ├── repository.py        # SQLite persistence
│   │   ├── schemas.py           # Pydantic models
│   │   ├── config.py
│   │   ├── db/                  # SQLAlchemy models + session
│   │   └── agents/
│   │       ├── qualification_agent.py
│   │       ├── outreach_agent.py
│   │       └── recommendation_agent.py
│   ├── tests/
│   │   └── test_evaluation.py
│   ├── data/gtm.db              # SQLite DB
│   └── requirements.txt
└── frontend/
    ├── app/
    │   ├── page.tsx             # דף ראשי
    │   └── layout.tsx
    ├── components/              # 6 קומפוננטות
    └── lib/
        ├── api.ts
        └── utils.ts
```

---

## 7. איך להריץ

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

פתח: **http://localhost:3000**

---

## 8. דוגמת flow מלא

**קלט:**
```
Company: Acme
Industry: SaaS
Employees: 100
Message: "We are looking for a project management solution."
```

**Qualification:**
```json
{ "qualified": true, "score": 88, "reason": "Strong fit for collaboration tools" }
```

**Outreach:**
```json
{
  "email": "Subject: Following up...",
  "linkedin": "Saw your inquiry from Acme...",
  "questions": ["What prompted you...", "..."]
}
```

**Recommendation:**
```json
{ "next_action": "book_meeting" }
```

---

## 9. מה עדיין לא נבנה

- **A/B prompt testing** — השוואת גרסאות פרומפט
- **LangGraph** — workflow graph במקום pipeline סדרתי
- **Tool calling** — חיפוש מידע על חברות (Clearbit, LinkedIn וכו')
- **RAG** — retrieval ממסמכי מוצר (vector DB + embeddings)
- **Agent Confidence Score** — מדד ביטחון הסוכן
- **Human-in-the-Loop** — review ידני לפני פעולה
- **CRM integration** — חיבור ל-Salesforce/HubSpot
- **Authentication / multi-tenant**

---

## 10. KPIs עסקיים — מטרות (מהחזון)

| KPI | סטטוס |
|-----|--------|
| Qualification Rate | ✅ מיושם |
| Meeting Recommendation Rate | ✅ מיושם |
| Average Lead Score | ✅ מיושם |
| Agent Processing Time | ✅ מיושם (processing_time_ms) |
| Agent Confidence Score | 🔜 |
| Human Review Rate | 🔜 |
| Prompt Win Rate | 🔜 (Phase 4) |

---

*מסמך זה משקף את מצב הפרויקט נכון ל-Phase 3.*
