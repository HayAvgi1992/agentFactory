"""LangGraph workflow tests for Phase 4."""

from app.graph import AGENT_STEPS, build_graph
from app.state import initial_state


def test_graph_has_seven_agent_steps():
    assert len(AGENT_STEPS) == 7
    step_ids = [step_id for step_id, _, _ in AGENT_STEPS]
    assert step_ids == [
        "planner",
        "research",
        "qualification",
        "product_fit",
        "outreach",
        "recommendation",
        "evaluation",
    ]


def test_graph_compiles():
    graph = build_graph()
    assert graph is not None


def test_pipeline_mock_run_produces_full_state():
    from app.pipeline import run_pipeline

    result = run_pipeline(
        {
            "company_name": "Acme",
            "industry": "SaaS",
            "company_size": "100",
            "message": "We need a project management solution with demo and pricing.",
        }
    )

    assert len(result.runs) == 7
    assert result.results.planner is not None
    assert result.results.research is not None
    assert result.results.product_fit is not None
    assert result.results.evaluation is not None
    assert result.results.qualification.qualified is True
    assert result.results.recommendation.next_action in {
        "book_meeting",
        "send_email",
        "nurture",
        "reject",
        "human_review",
    }
