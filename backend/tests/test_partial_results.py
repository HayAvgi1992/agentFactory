"""Partial results assembly tests."""

from app.results_builder import build_agent_results_from_state


def test_partial_pipeline_state_returns_completed_steps():
    state = {
        "lead": {"company_name": "Acme", "message": "demo please"},
        "planner": {"required_sources": ["crm_accounts"], "reasoning": "plan"},
        "research": {"retrieved_documents": ["acme"], "reasoning": "research"},
        "retrieved_context": [],
        "qualification": {
            "qualified": True,
            "score": 80,
            "reason": "Good fit",
            "signals": [],
            "risks": [],
        },
        "pipeline_error": {
            "step_index": 4,
            "step_id": "product_fit",
            "message": "Simulated failure",
        },
    }
    results = build_agent_results_from_state(state, processing_time_ms=5000)
    assert results is not None
    assert results.qualification.score == 80
    assert results.planner is not None
    assert results.research is not None
    assert results.product_fit is None
    assert results.outreach is None
    assert results.recommendation is None
