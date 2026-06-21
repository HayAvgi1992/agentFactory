"""SQLite-backed lead and agent run persistence."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.db.models import AgentRun, Lead
from app.pipeline import AgentRunRecord
from app.schemas import (
    AgentResults,
    LeadCreate,
    LeadResponse,
    OutreachOutput,
    QualificationOutput,
    RecommendationOutput,
)

AGENT_ORDER = ("qualification", "outreach", "recommendation")


def create_lead(db: Session, data: LeadCreate) -> Lead:
    lead = Lead(
        company_name=data.company_name,
        industry=data.industry,
        company_size=data.company_size,
        message=data.message,
    )
    db.add(lead)
    db.flush()
    return lead


def save_agent_runs(db: Session, lead_id: int, runs: List[AgentRunRecord]) -> None:
    for run in runs:
        db.add(
            AgentRun(
                lead_id=lead_id,
                agent_name=run.agent_name,
                input=run.input,
                output=run.output,
            )
        )


def list_leads(db: Session) -> List[LeadResponse]:
    leads = (
        db.query(Lead)
        .options(joinedload(Lead.agent_runs))
        .order_by(Lead.id.desc())
        .all()
    )
    return [_to_response(lead) for lead in leads]


def get_lead(db: Session, lead_id: int) -> Optional[LeadResponse]:
    lead = (
        db.query(Lead)
        .options(joinedload(Lead.agent_runs))
        .filter(Lead.id == lead_id)
        .first()
    )
    if not lead:
        return None
    return _to_response(lead)


def count_leads(db: Session) -> int:
    return db.query(Lead).count()


def _build_agent_results(runs: List[AgentRun]) -> Optional[AgentResults]:
    by_name = {run.agent_name: run for run in runs}
    if not all(name in by_name for name in AGENT_ORDER):
        return None

    qualification = by_name["qualification"].output
    outreach = by_name["outreach"].output
    recommendation = by_name["recommendation"].output

    first_at = by_name["qualification"].created_at
    last_at = by_name["recommendation"].created_at
    processing_time_ms = int((last_at - first_at).total_seconds() * 1000)

    return AgentResults(
        qualification=QualificationOutput(
            qualified=bool(qualification["qualified"]),
            score=int(qualification["score"]),
            reason=str(qualification["reason"]),
        ),
        outreach=OutreachOutput(
            email=str(outreach["email"]),
            linkedin=str(outreach["linkedin"]),
            questions=list(outreach["questions"]),
        ),
        recommendation=RecommendationOutput(
            next_action=str(recommendation["next_action"]),
        ),
        processing_time_ms=processing_time_ms,
    )


def _to_response(lead: Lead, results_override: Optional[AgentResults] = None) -> LeadResponse:
    results = results_override if results_override is not None else _build_agent_results(lead.agent_runs)
    return LeadResponse(
        id=lead.id,
        company_name=lead.company_name,
        industry=lead.industry,
        company_size=lead.company_size,
        message=lead.message,
        created_at=lead.created_at,
        results=results,
    )


def lead_to_response(lead: Lead, pipeline_results: Optional[AgentResults] = None) -> LeadResponse:
    """Build response after submit, using pipeline timing when available."""
    return _to_response(lead, results_override=pipeline_results)
