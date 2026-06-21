"""Shared GTMState tests (vision §5)."""

from app.state import (
    AGENT_READS,
    AGENT_WRITES,
    SHARED_STATE_FIELDS,
    agent_output_from_state,
    build_state_snapshot,
    get_lead,
    get_qualification,
    initial_state,
    populated_field_count,
    public_state_snapshot,
    snapshot_for_agent,
)


def test_initial_state_has_lead_and_empty_context():
    state = initial_state({"company_name": "Acme", "message": "hello"})
    assert get_lead(state)["company_name"] == "Acme"
    assert state["retrieved_context"] == []
    assert state["agent_runs"] == []


def test_snapshot_for_agent_uses_read_matrix():
    state = initial_state({"company_name": "Acme", "message": "hello"})
    state["planner"] = {"required_sources": ["crm_accounts"]}
    state["retrieved_context"] = [{"source": "crm_accounts", "document_id": "acme"}]

    qual_snapshot = snapshot_for_agent(state, "qualification")
    assert "lead" in qual_snapshot
    assert "retrieved_context" in qual_snapshot
    assert "planner" not in qual_snapshot

    research_snapshot = snapshot_for_agent(state, "planner")
    assert list(research_snapshot.keys()) == ["lead"]


def test_public_snapshot_tracks_populated_fields():
    state = initial_state({"company_name": "Acme", "message": "hello"})
    state["qualification"] = {"qualified": True, "score": 80, "reason": "ok"}

    raw = public_state_snapshot(state)
    assert "lead" in raw["populated_fields"]
    assert "qualification" in raw["populated_fields"]
    assert populated_field_count(state) == 2


def test_build_state_snapshot_from_full_graph_state():
    from app.graph import build_graph

    final = build_graph().invoke(
        initial_state(
            {
                "company_name": "Acme",
                "industry": "SaaS",
                "message": "Need demo and pricing for project management.",
            }
        )
    )
    snapshot = build_state_snapshot(final)

    assert snapshot.lead["company_name"] == "Acme"
    assert "qualification" in snapshot.populated_fields
    assert get_qualification(final)["score"] > 0
    assert len(snapshot.populated_fields) >= len(SHARED_STATE_FIELDS) - 2


def test_agent_access_matrix_covers_all_agents():
    agents = set(AGENT_READS) | set(AGENT_WRITES)
    expected = {
        "planner",
        "research",
        "qualification",
        "product_fit",
        "outreach",
        "recommendation",
        "evaluation",
    }
    assert agents == expected


def test_agent_output_from_state_research():
    state = initial_state({"company_name": "Acme", "message": "hi"})
    state["research"] = {"retrieved_documents": ["acme"]}
    state["retrieved_context"] = [{"source": "crm_accounts", "document_id": "acme"}]

    output = agent_output_from_state(state, "research")
    assert output["retrieved_documents"] == ["acme"]
    assert len(output["retrieved_context"]) == 1
