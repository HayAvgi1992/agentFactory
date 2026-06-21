"""Persistence tests for Phase 2+."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import AgentRun, Lead
from app.pipeline import AgentRunRecord
from app.repository import (
    _build_agent_results,
    create_lead,
    get_lead,
    list_leads,
    save_agent_runs,
)
from app.schemas import LeadCreate


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def _full_runs(
    qualified: bool = True,
    score: int = 88,
    next_action: str = "book_meeting",
) -> list[AgentRunRecord]:
    return [
        AgentRunRecord(
            agent_name="planner",
            input={"lead": {"company_name": "Acme"}},
            output={"required_sources": ["crm_accounts", "product_catalog"]},
        ),
        AgentRunRecord(
            agent_name="research",
            input={"lead": {"company_name": "Acme"}, "planner": {}},
            output={
                "retrieved_documents": ["acme", "monday_crm"],
                "retrieved_context": [
                    {
                        "source": "crm_accounts",
                        "document_id": "acme",
                        "title": "Acme",
                        "snippet": "CRM account notes",
                    }
                ],
            },
        ),
        AgentRunRecord(
            agent_name="qualification",
            input={},
            output={
                "qualified": qualified,
                "score": score,
                "reason": "Strong fit",
                "signals": ["ICP fit"],
                "risks": [],
                "reasoning": "Strong fit",
            },
        ),
        AgentRunRecord(
            agent_name="product_fit",
            input={},
            output={
                "recommended_product": "Monday CRM",
                "alternative_products": ["Work Management"],
                "confidence": 0.91,
                "matching_requirements": ["Pipeline visibility"],
                "reasoning": "CRM fit",
            },
        ),
        AgentRunRecord(
            agent_name="outreach",
            input={},
            output={"email": "Hi", "linkedin": "Hello", "questions": ["Q1"]},
        ),
        AgentRunRecord(
            agent_name="recommendation",
            input={},
            output={"next_action": next_action},
        ),
        AgentRunRecord(
            agent_name="evaluation",
            input={},
            output={
                "confidence": 0.88,
                "needs_human_review": False,
                "missing_information": ["budget"],
            },
        ),
    ]


def test_create_lead_and_agent_runs():
    db = _make_session()
    data = LeadCreate(
        company_name="Acme",
        industry="SaaS",
        company_size="100",
        message="Looking for a project management solution.",
    )
    lead = create_lead(db, data)
    db.commit()

    save_agent_runs(db, lead.id, _full_runs())
    db.commit()

    stored = get_lead(db, lead.id)
    assert stored is not None
    assert stored.company_name == "Acme"
    assert stored.results is not None
    assert stored.results.qualification.score == 88
    assert stored.results.product_fit is not None
    assert stored.results.product_fit.recommended_product == "Monday CRM"
    assert stored.results.recommendation.next_action == "book_meeting"
    assert stored.results.evaluation is not None
    assert stored.results.evaluation.confidence == 0.88


def test_list_leads_newest_first():
    db = _make_session()
    for name in ("First", "Second"):
        lead = create_lead(
            db,
            LeadCreate(company_name=name, message="test message"),
        )
        save_agent_runs(db, lead.id, _full_runs(score=70, next_action="send_email"))
    db.commit()

    leads = list_leads(db)
    assert [l.company_name for l in leads] == ["Second", "First"]


def test_partial_runs_return_no_results():
    runs = [
        AgentRun(
            lead_id=1,
            agent_name="qualification",
            input={},
            output={"qualified": True, "score": 80, "reason": "ok"},
        ),
    ]
    assert _build_agent_results(runs) is None


def test_legacy_three_agent_runs_still_load():
    runs = [
        AgentRun(
            lead_id=1,
            agent_name="qualification",
            input={},
            output={"qualified": True, "score": 80, "reason": "ok"},
        ),
        AgentRun(
            lead_id=1,
            agent_name="outreach",
            input={},
            output={"email": "e", "linkedin": "l", "questions": []},
        ),
        AgentRun(
            lead_id=1,
            agent_name="recommendation",
            input={},
            output={"next_action": "send_email"},
        ),
    ]
    results = _build_agent_results(runs)
    assert results is not None
    assert results.qualification.score == 80
    assert results.product_fit is None
    assert results.evaluation is None
