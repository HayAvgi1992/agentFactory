"""Persistence tests for Phase 2."""

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

    runs = [
        AgentRunRecord(
            agent_name="qualification",
            input={"company_name": "Acme"},
            output={"qualified": True, "score": 88, "reason": "Strong fit"},
        ),
        AgentRunRecord(
            agent_name="outreach",
            input={"lead_data": {}, "qualification": {}},
            output={"email": "Hi", "linkedin": "Hello", "questions": ["Q1"]},
        ),
        AgentRunRecord(
            agent_name="recommendation",
            input={"lead_data": {}, "qualification": {}, "outreach": {}},
            output={"next_action": "book_meeting"},
        ),
    ]
    save_agent_runs(db, lead.id, runs)
    db.commit()

    stored = get_lead(db, lead.id)
    assert stored is not None
    assert stored.company_name == "Acme"
    assert stored.results is not None
    assert stored.results.qualification.score == 88
    assert stored.results.recommendation.next_action == "book_meeting"


def test_list_leads_newest_first():
    db = _make_session()
    for name in ("First", "Second"):
        lead = create_lead(
            db,
            LeadCreate(company_name=name, message="test message"),
        )
        save_agent_runs(
            db,
            lead.id,
            [
                AgentRunRecord("qualification", {}, {"qualified": True, "score": 70, "reason": "ok"}),
                AgentRunRecord("outreach", {}, {"email": "e", "linkedin": "l", "questions": []}),
                AgentRunRecord("recommendation", {}, {"next_action": "send_email"}),
            ],
        )
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
