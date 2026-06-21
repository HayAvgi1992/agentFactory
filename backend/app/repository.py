"""SQLite-backed lead and agent run persistence."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.db.models import AgentRun, Lead
from app.pipeline import AgentRunRecord
from app.schemas import (
    AgentResults,
    EvaluationAgentOutput,
    LeadCreate,
    LeadResponse,
    OutreachOutput,
    PlannerOutput,
    ProductFitOutput,
    QualificationOutput,
    RecommendationOutput,
    ResearchOutput,
    RetrievedContextItem,
)

AGENT_ORDER = (
    "planner",
    "research",
    "qualification",
    "product_fit",
    "outreach",
    "recommendation",
    "evaluation",
)
LEGACY_AGENT_ORDER = ("qualification", "outreach", "recommendation")


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

    if all(name in by_name for name in AGENT_ORDER):
        return _build_full_results(by_name)
    if all(name in by_name for name in LEGACY_AGENT_ORDER):
        return _build_legacy_results(by_name)
    return None


def _build_full_results(by_name: dict) -> AgentResults:
    qualification = by_name["qualification"].output
    outreach = by_name["outreach"].output
    recommendation = by_name["recommendation"].output
    planner = by_name["planner"].output
    research = by_name["research"].output
    product_fit = by_name["product_fit"].output
    evaluation = by_name["evaluation"].output

    research_run = by_name["research"]
    retrieved_context = _extract_retrieved_context(research_run)

    first_at = by_name["planner"].created_at
    last_at = by_name["evaluation"].created_at
    processing_time_ms = int((last_at - first_at).total_seconds() * 1000)

    return AgentResults(
        planner=PlannerOutput(required_sources=list(planner.get("required_sources", []))),
        research=ResearchOutput(
            retrieved_documents=list(research.get("retrieved_documents", [])),
        ),
        qualification=_qualification_from_output(qualification),
        product_fit=ProductFitOutput(
            recommended_product=str(product_fit.get("recommended_product", "")),
            alternative_products=list(product_fit.get("alternative_products", [])),
            confidence=float(product_fit.get("confidence", 0)),
            matching_requirements=list(product_fit.get("matching_requirements", [])),
            reasoning=str(product_fit.get("reasoning", "")),
        ),
        outreach=OutreachOutput(
            email=str(outreach["email"]),
            linkedin=str(outreach["linkedin"]),
            questions=list(outreach["questions"]),
        ),
        recommendation=RecommendationOutput(
            next_action=str(recommendation["next_action"]),
        ),
        evaluation=EvaluationAgentOutput(
            confidence=float(evaluation.get("confidence", 0)),
            needs_human_review=bool(evaluation.get("needs_human_review", False)),
            missing_information=list(evaluation.get("missing_information", [])),
        ),
        retrieved_context=retrieved_context,
        processing_time_ms=processing_time_ms,
    )


def _build_legacy_results(by_name: dict) -> AgentResults:
    qualification = by_name["qualification"].output
    outreach = by_name["outreach"].output
    recommendation = by_name["recommendation"].output

    first_at = by_name["qualification"].created_at
    last_at = by_name["recommendation"].created_at
    if first_at and last_at:
        processing_time_ms = int((last_at - first_at).total_seconds() * 1000)
    else:
        processing_time_ms = 0

    return AgentResults(
        qualification=_qualification_from_output(qualification),
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


def _qualification_from_output(qualification: dict) -> QualificationOutput:
    reasoning = qualification.get("reasoning", qualification.get("reason", ""))
    return QualificationOutput(
        qualified=bool(qualification["qualified"]),
        score=int(qualification["score"]),
        reason=str(qualification.get("reason", reasoning)),
        signals=list(qualification.get("signals", [])),
        risks=list(qualification.get("risks", [])),
        reasoning=str(reasoning),
    )


def _extract_retrieved_context(research_run: AgentRun) -> List[RetrievedContextItem]:
    items: List[RetrievedContextItem] = []
    context_entries = research_run.output.get("retrieved_context") or []
    for entry in context_entries:
        items.append(
            RetrievedContextItem(
                source=str(entry.get("source", "")),
                document_id=str(entry.get("document_id", "")),
                title=str(entry.get("title", "")),
                snippet=str(entry.get("snippet", "")),
            )
        )
    return items


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
