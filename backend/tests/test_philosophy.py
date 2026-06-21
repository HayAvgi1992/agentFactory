"""Agent philosophy tests — reasoning fields present in mock pipeline (vision §6)."""

from app.pipeline import run_pipeline


def test_mock_pipeline_includes_reasoning_fields():
    result = run_pipeline(
        {
            "company_name": "Acme",
            "industry": "SaaS",
            "company_size": "100",
            "message": "We need demo and pricing for project management.",
        }
    )
    assert result.status == "complete"
    assert result.results is not None

    q = result.results.qualification
    assert q.reasoning
    assert isinstance(q.patterns, list)
    assert isinstance(q.tradeoffs, list)

    assert result.results.planner is not None
    assert result.results.planner.reasoning

    assert result.results.recommendation.reasoning
    assert result.results.evaluation is not None
    assert result.results.evaluation.reasoning
