"""Evaluation metrics tests for Phase 3+."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.evaluation import compute_evaluation_metrics
from app.repository import create_lead, save_agent_runs
from app.schemas import AgentRunRecord, LeadCreate


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def _complete_runs(
    qualified: bool,
    score: int,
    next_action: str = "send_email",
    *,
    confidence: float = 0.85,
    needs_human_review: bool = False,
) -> list[AgentRunRecord]:
    return [
        AgentRunRecord(agent_name="planner", input={}, output={"required_sources": ["product_catalog"]}),
        AgentRunRecord(
            agent_name="research",
            input={},
            output={"retrieved_documents": ["monday_crm"], "retrieved_context": []},
        ),
        AgentRunRecord(
            agent_name="qualification",
            input={},
            output={"qualified": qualified, "score": score, "reason": "ok"},
        ),
        AgentRunRecord(
            agent_name="product_fit",
            input={},
            output={
                "recommended_product": "Monday CRM",
                "confidence": 0.9,
                "matching_requirements": [],
                "reasoning": "fit",
            },
        ),
        AgentRunRecord(agent_name="outreach", input={}, output={"email": "e", "linkedin": "l", "questions": []}),
        AgentRunRecord(agent_name="recommendation", input={}, output={"next_action": next_action}),
        AgentRunRecord(
            agent_name="evaluation",
            input={},
            output={
                "confidence": confidence,
                "needs_human_review": needs_human_review,
                "missing_information": [],
            },
        ),
    ]


def test_empty_db_returns_zeros():
    db = _make_session()
    metrics = compute_evaluation_metrics(db)

    assert metrics.total_leads == 0
    assert metrics.qualified_leads == 0
    assert metrics.qualification_rate == 0.0
    assert metrics.meeting_recommendations == 0
    assert metrics.meeting_recommendation_rate == 0.0
    assert metrics.average_score is None
    assert metrics.processed_leads == 0
    assert metrics.average_confidence is None
    assert metrics.human_review_count == 0


def test_mixed_qualification_rates():
    db = _make_session()
    configs = [(True, 80), (True, 60), (False, 40)]
    for i, (qualified, score) in enumerate(configs):
        lead = create_lead(db, LeadCreate(company_name=f"Lead{i}", message="test"))
        save_agent_runs(db, lead.id, _complete_runs(qualified, score))
    db.commit()

    metrics = compute_evaluation_metrics(db)

    assert metrics.total_leads == 3
    assert metrics.qualified_leads == 2
    assert abs(metrics.qualification_rate - 2 / 3) < 0.001
    assert metrics.average_score == 60.0
    assert metrics.processed_leads == 3


def test_meeting_recommendation_rate():
    db = _make_session()
    actions = ["book_meeting", "send_email", "nurture"]
    for i, action in enumerate(actions):
        lead = create_lead(db, LeadCreate(company_name=f"Lead{i}", message="test"))
        save_agent_runs(db, lead.id, _complete_runs(True, 70, next_action=action))
    db.commit()

    metrics = compute_evaluation_metrics(db)

    assert metrics.meeting_recommendations == 1
    assert abs(metrics.meeting_recommendation_rate - 1 / 3) < 0.001


def test_partial_pipeline_counts_qualification_not_meeting():
    db = _make_session()
    lead = create_lead(db, LeadCreate(company_name="Partial", message="test"))
    save_agent_runs(
        db,
        lead.id,
        [
            AgentRunRecord(
                agent_name="qualification",
                input={},
                output={"qualified": True, "score": 88, "reason": "Strong fit"},
            ),
        ],
    )
    db.commit()

    metrics = compute_evaluation_metrics(db)

    assert metrics.total_leads == 1
    assert metrics.qualified_leads == 0
    assert metrics.qualification_rate == 0.0
    assert metrics.meeting_recommendations == 0
    assert metrics.meeting_recommendation_rate == 0.0
    assert metrics.average_score is None
    assert metrics.processed_leads == 0


def test_lead_ids_filter():
    db = _make_session()
    ids = []
    for name in ("A", "B", "C"):
        lead = create_lead(db, LeadCreate(company_name=name, message="test"))
        save_agent_runs(db, lead.id, _complete_runs(True, 50))
        ids.append(lead.id)
    db.commit()

    metrics = compute_evaluation_metrics(db, lead_ids=[ids[0], ids[2]])

    assert metrics.total_leads == 2
    assert metrics.qualified_leads == 2
    assert metrics.average_score == 50.0


def test_confidence_and_human_review_metrics():
    db = _make_session()
    configs = [
        (0.9, False),
        (0.7, True),
        (0.8, False),
    ]
    for i, (confidence, needs_review) in enumerate(configs):
        lead = create_lead(db, LeadCreate(company_name=f"Lead{i}", message="test"))
        save_agent_runs(
            db,
            lead.id,
            _complete_runs(
                True,
                70,
                confidence=confidence,
                needs_human_review=needs_review,
            ),
        )
    db.commit()

    metrics = compute_evaluation_metrics(db)

    assert abs(metrics.average_confidence - 0.8) < 0.001
    assert metrics.human_review_count == 1
    assert abs(metrics.human_review_rate - 1 / 3) < 0.001
