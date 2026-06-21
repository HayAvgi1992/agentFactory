"""Product Fit Agent tests — vision §8."""

from app.agents.product_fit_agent import run_product_fit_agent
from app.pipeline import run_pipeline
from app.state import initial_state


def _fit(lead_data: dict, qualification: dict | None = None) -> dict:
    from app.agents.planner_agent import run_planner_agent
    from app.agents.research_agent import run_research_agent

    state = initial_state(lead_data)
    state = {**state, "planner": run_planner_agent(state)}
    research = run_research_agent(state)
    state = {
        **state,
        "retrieved_context": research["retrieved_context"],
        "research": research,
    }
    if qualification is None:
        from app.agents.qualification_agent import run_qualification_agent

        qualification = run_qualification_agent(state)
    state = {**state, "qualification": qualification}
    return run_product_fit_agent(state)


def test_acme_recommends_work_management():
    result = _fit(
        {
            "company_name": "Acme",
            "industry": "SaaS",
            "company_size": "100",
            "message": "We are looking for a project management solution.",
        }
    )
    assert result["recommended_product"] == "Work Management"
    assert "Monday CRM" in result["alternative_products"]
    assert result["reasoning"]
    assert "align" in result["reasoning"].lower()
    assert "Product Documentation" in result["context_inputs"] or "Case Studies" in result["context_inputs"]
    assert result["matching_requirements"]


def test_fintech_crm_message_recommends_monday_crm():
    result = _fit(
        {
            "company_name": "NovaPay",
            "industry": "fintech",
            "company_size": "250",
            "message": "We need CRM pipeline visibility and lead tracking for our sales team.",
        },
        qualification={
            "qualified": True,
            "score": 80,
            "signals": ["Strong ICP fit"],
            "risks": [],
            "reasoning": "Good fit",
        },
    )
    assert result["recommended_product"] == "Monday CRM"
    assert "Pipeline visibility" in result["matching_requirements"]


def test_product_fit_includes_qualification_input():
    result = _fit(
        {
            "company_name": "Acme",
            "industry": "SaaS",
            "message": "project management",
        }
    )
    assert "Lead Information" in result["context_inputs"]
    assert "Qualification Output" in result["context_inputs"]


def test_full_pipeline_product_fit_shape():
    result = run_pipeline(
        {
            "company_name": "Acme",
            "industry": "SaaS",
            "company_size": "100",
            "message": "We need demo and pricing for project management.",
        }
    )
    assert result.status == "complete"
    fit = result.results.product_fit
    assert fit is not None
    assert fit.recommended_product
    assert fit.confidence > 0
    assert fit.reasoning
    assert fit.context_inputs
