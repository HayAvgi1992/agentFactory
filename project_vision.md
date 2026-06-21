# GTM Agent Factory — Project Vision

> Version 2.0
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
* Optimize business KPIs

The project should demonstrate practical AI Product Engineering capabilities including:

* Agent Engineering
* LangGraph
* Tool Calling
* RAG
* Embeddings
* Vector Search
* Evaluation Frameworks
* Prompt Experimentation
* Business KPI Optimization

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

# 3. Current State

Current implementation includes:

✅ Qualification Agent

✅ Outreach Agent

✅ Recommendation Agent

✅ SQLite Persistence

✅ Evaluation Dashboard

✅ KPI Tracking

Current architecture:

```text
Lead
↓
Qualification Agent
↓
Outreach Agent
↓
Recommendation Agent
```

This serves as the foundation for the next phase.

---

# 4. Target Architecture

Future architecture:

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

All agents share a common state.

The system should evolve from a simple pipeline into a true Agentic Workflow.

---

# 5. Shared State

All agents operate on a shared LangGraph state.

```python
class GTMState(TypedDict):
    lead: dict
    retrieved_context: list
    qualification: dict
    product_fit: dict
    outreach: dict
    recommendation: dict
    evaluation: dict
```

Every agent reads and updates state.

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

---

# 20. Development Roadmap

Phase 1

✅ Basic Agent Pipeline

Phase 2

✅ Persistence Layer

Phase 3

✅ Evaluation Dashboard

Phase 4

✅ Prompt Experimentation & A/B Testing

Phase 5

✅ LangGraph Migration

Phase 6

✅ Knowledge Base + Local RAG (ChromaDB + embeddings)

Phase 7

✅ Tool Calling + Research Agent

Phase 8

✅ Observability + Human Review

Phase 9

🔜 Production Readiness (auth, CRM integrations, deployment — out of portfolio scope)

**Portfolio demo status (2025):** Phases 1–8 complete for demo purposes. Phase 9 intentionally deferred.

---

# 21. Final Goal

Build a production-style AI GTM platform that demonstrates:

* Agent Engineering
* LangGraph Workflows
* Tool Calling
* RAG
* Embeddings
* Vector Databases
* Evaluation
* Experimentation
* Business Impact

The system should resemble the architecture and product-thinking behind modern AI Revenue organizations such as monday.com's RevAI.
