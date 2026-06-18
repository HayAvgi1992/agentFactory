# GTM Agent Factory

## Project Goal

Build an AI-native GTM (Go-To-Market) platform inspired by monday.com's RevAI organization.

The purpose of the project is NOT to build another chatbot.

The purpose is to demonstrate the ability to:

* Take a business problem
* Design an AI-powered workflow
* Build production-like agent systems
* Measure business impact
* Experiment and iterate

This project should showcase skills relevant for AI Product Engineering, Agent Engineering and AI System Design.

---

# Core Business Problem

Sales teams spend significant time:

* Researching leads
* Qualifying leads
* Prioritizing opportunities
* Writing outreach messages
* Deciding which leads deserve a meeting

The goal is to automate the first stages of the sales funnel using AI Agents.

---

# Success Criteria

The project should answer:

"How can AI increase GTM productivity and conversion?"

Business KPIs:

* Qualification Rate
* Meeting Recommendation Rate
* Average Lead Score
* Prompt Win Rate
* Agent Execution Time

---

# High Level Architecture

Frontend (Next.js)
|
FastAPI Backend
|
Agent Orchestrator
|
-

| | | |
Research Qualification Outreach Recommendation
Agent Agent Agent Agent
|
OpenAI

---

# Phase 1 - MVP

Goal:
Build a complete workflow as quickly as possible.

Do NOT use:

* LangGraph
* RAG
* Vector DB
* Embeddings

Keep it simple.

---

## Feature 1 - Lead Submission

User enters:

* Company Name
* Industry
* Company Size
* Lead Message

Example:

Company: Acme

Industry: SaaS

Employees: 100

Message:
"We are looking for a project management solution."

---

## Feature 2 - Qualification Agent

Input:

Lead

Output:

{
"qualified": true,
"score": 88,
"reason": "Strong fit for collaboration tools"
}

Requirements:

* Structured JSON output
* Score between 0-100
* Qualification decision

---

## Feature 3 - Outreach Agent

Generate:

* First Email
* LinkedIn Message
* Discovery Questions

Output:

{
"email": "...",
"linkedin": "...",
"questions": [...]
}

---

## Feature 4 - Recommendation Agent

Output:

{
"next_action": "book_meeting"
}

Possible actions:

* reject
* nurture
* send_email
* book_meeting

---

## MVP Dashboard

Display:

* Lead
* Score
* Qualification
* Recommendation

---

## Agent Pipeline Diagram

Visual card showing the sequential workflow:

```
Lead Input
    ↓
Qualification Agent  (qualified · score · reason)
    ↓
Outreach Agent       (email · linkedin · questions)
    ↓
Recommendation Agent (next_action)
```

Purpose:

* Help users understand the agent flow at a glance
* Show live status: Pending → Running → Complete
* Surface key outputs on the diagram after a lead is processed

---

# Phase 2 - Persistence

Goal:
Store everything.

Database:

SQLite initially.

Future:

PostgreSQL.

Tables:

## leads

id
company_name
industry
company_size
message
created_at

---

## agent_runs

id
lead_id
agent_name
input
output
created_at

---

Store every agent execution.

This becomes the foundation for evaluation.

---

# Phase 3 - Evaluation Layer

Goal:
Demonstrate AI Engineering maturity.

Create metrics:

Qualification Rate

qualified leads / total leads

Meeting Recommendation Rate

meeting recommendations / total leads

Average Lead Score

average score across all leads

---

Dashboard should show:

* Total Leads
* Qualified Leads
* Average Score
* Meeting Recommendation Rate

---

# Phase 4 - Prompt A/B Testing

Goal:
Simulate real-world AI experimentation.

Create:

Prompt A

Prompt B

Run both prompts on the same lead.

Store results.

Example:

Prompt A:

Conservative Qualification

Prompt B:

Aggressive Qualification

Compare:

* Qualification Rate
* Meeting Recommendation Rate
* Average Lead Score

Display winner.

This is one of the most important features.

---

# Phase 5 - LangGraph Migration

Goal:
Introduce Agent Frameworks.

Current Flow:

Lead
↓
Qualification
↓
Outreach
↓
Recommendation

Replace with:

LangGraph State Machine

START
↓
Research
↓
Qualification
↓
Outreach
↓
Recommendation
↓
END

Purpose:

* State Management
* Agent Orchestration
* Future Extensibility

---

# Phase 6 - Tool Calling

Goal:
Create real agent behavior.

Research Agent may use tools.

Examples:

search_company()

get_company_profile()

lookup_industry()

Agent decides:

* Which tool to call
* When to call it
* How to use returned data

---

# Phase 7 - RAG

Only after previous phases are complete.

Create knowledge base:

* Product Documentation
* Pricing Information
* Case Studies
* Use Cases

Pipeline:

Documents
↓
Chunking
↓
Embeddings
↓
Vector Database
↓
Retrieval
↓
Agent

Purpose:

Generate more accurate recommendations.

---

# Phase 8 - Production AI Features

Potential future additions:

* Human-in-the-loop approval
* Multi-agent collaboration
* MCP integrations
* Email sending
* Calendar booking
* Salesforce integration
* HubSpot integration
* Agent monitoring
* Agent observability

---

# Recommended Tech Stack

Frontend

* Next.js
* TypeScript
* TailwindCSS
* React Query

Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic

Database

* SQLite (MVP)
* PostgreSQL (Future)

AI

* OpenAI SDK
* Structured Outputs

Future AI Stack

* LangGraph
* ChromaDB
* OpenAI Embeddings

Deployment

Frontend:
Vercel

Backend:
Render or Railway

---

# What Matters Most

The goal is NOT:

"Look, I used a Vector Database."

The goal IS:

"Look, I built an AI system that solves a business problem, measures impact, and supports experimentation."

Focus order:

1. Business Workflow
2. Agent Outputs
3. Evaluation
4. A/B Testing
5. LangGraph
6. Tool Calling
7. RAG
8. Advanced AI Infrastructure

Always optimize for measurable business impact over technical complexity.
