"""SQLite-backed lead and agent run persistence."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.db.models import AgentRun, Lead
from app.results_builder import build_agent_results_from_runs
from app.schemas import AgentResults, AgentRunRecord, LeadCreate, LeadResponse, PipelineStatus


def create_lead(db: Session, data: LeadCreate) -> Lead:
    lead = Lead(
        company_name=data.company_name,
        industry=data.industry,
        company_size=data.company_size,
        message=data.message,
        pipeline_status="pending",
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


def update_lead_pipeline(
    db: Session,
    lead_id: int,
    *,
    status: PipelineStatus,
    error: Optional[str] = None,
    step_id: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
) -> None:
    lead = db.query(Lead).filter(Lead.id == lead_id).one()
    lead.pipeline_status = status
    lead.pipeline_error = error
    lead.pipeline_step_id = step_id
    lead.processing_time_ms = processing_time_ms


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


def _to_response(lead: Lead, results_override: Optional[AgentResults] = None) -> LeadResponse:
    results = results_override
    if results is None:
        results = build_agent_results_from_runs(
            lead.agent_runs,
            processing_time_ms=lead.processing_time_ms,
        )

    return LeadResponse(
        id=lead.id,
        company_name=lead.company_name,
        industry=lead.industry,
        company_size=lead.company_size,
        message=lead.message,
        created_at=lead.created_at,
        pipeline_status=lead.pipeline_status,  # type: ignore[arg-type]
        pipeline_error=lead.pipeline_error,
        pipeline_step_id=lead.pipeline_step_id,
        processing_time_ms=lead.processing_time_ms,
        results=results,
    )


def lead_to_response(
    lead: Lead,
    pipeline_results: Optional[AgentResults] = None,
    *,
    pipeline_status: PipelineStatus = "complete",
    pipeline_error: Optional[str] = None,
    pipeline_step_id: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
) -> LeadResponse:
    """Build response after submit, using pipeline output when available."""
    response = _to_response(lead, results_override=pipeline_results)
    return response.model_copy(
        update={
            "pipeline_status": pipeline_status,
            "pipeline_error": pipeline_error,
            "pipeline_step_id": pipeline_step_id,
            "processing_time_ms": processing_time_ms,
        }
    )
