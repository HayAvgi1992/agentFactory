"""Qualification Agent tests — vision §7."""

from app.agents.qualification_agent import run_qualification_agent
from app.agents.guardrails import QUALIFICATION_THRESHOLD
from app.pipeline import run_pipeline
from app.state import initial_state


def _qualify(lead_data: dict) -> dict:
    state = initial_state(lead_data)
    # Minimal upstream state: planner + research via full pipeline slice
    from app.agents.planner_agent import run_planner_agent
    from app.agents.research_agent import run_research_agent

    planner = run_planner_agent(state)
    state = {**state, "planner": planner}
    research = run_research_agent(state)
    state = {
        **state,
        "retrieved_context": research["retrieved_context"],
        "research": {
            "retrieved_documents": research["retrieved_documents"],
            "patterns_identified": research.get("patterns_identified", []),
            "reasoning": research.get("reasoning", ""),
        },
    }
    return run_qualification_agent(state)


def test_acme_qualified_with_strong_icp_and_crm():
    result = _qualify(
        {
            "company_name": "Acme",
            "industry": "SaaS",
            "company_size": "100",
            "message": "We are looking for a project management solution.",
        }
    )
    assert result["qualified"] is True
    assert result["score"] >= QUALIFICATION_THRESHOLD
    assert "Strong ICP fit" in result["signals"]
    assert result["reasoning"]
    assert "ideal customer profile" in result["reasoning"].lower() or "Acme" in result["reasoning"]
    assert "CRM Context" in result["context_inputs"]
    assert "Lead Information" in result["context_inputs"]


def test_weak_lead_not_qualified():
    result = _qualify(
        {
            "company_name": "GreenEnergy Ltd",
            "industry": "CleanTech",
            "company_size": "10-50",
            "message": "Saw your product mentioned in a blog. Can you send more info?",
        }
    )
    assert result["qualified"] is False
    assert result["score"] < QUALIFICATION_THRESHOLD
    assert any("outside core ICP" in r for r in result["risks"])
    assert result["reasoning"]


def test_job_seeker_disqualified():
    result = _qualify(
        {
            "company_name": "Unknown",
            "industry": "SaaS",
            "company_size": "5",
            "message": "I'm looking for a job at your company.",
        }
    )
    assert result["qualified"] is False
    assert result["score"] < QUALIFICATION_THRESHOLD
    assert any("Job-seeker" in r for r in result["risks"])


def test_playbook_scoring_signals_present():
    result = _qualify(
        {
            "company_name": "Acme",
            "industry": "SaaS",
            "company_size": "100",
            "message": "We need a demo and pricing ASAP this quarter.",
        }
    )
    assert result["score"] >= 75
    assert any("engagement" in s.lower() or "urgency" in s.lower() for s in result["signals"])


def test_full_pipeline_qualification_output_shape():
    result = run_pipeline(
        {
            "company_name": "Acme",
            "industry": "SaaS",
            "company_size": "100",
            "message": "We need demo and pricing for project management.",
        }
    )
    assert result.status == "complete"
    q = result.results.qualification
    assert q.qualified
    assert q.signals
    assert isinstance(q.risks, list)
    assert q.reasoning
    assert q.context_inputs
