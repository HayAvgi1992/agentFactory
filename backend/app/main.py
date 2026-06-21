from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db, init_db
from app.evaluation import compute_evaluation_metrics
from app.experiments import compare_prompt_versions, list_experiments
from app.pipeline import run_pipeline
from app.rag import get_rag_status, index_knowledge_base
from app.repository import (
    count_leads,
    create_lead,
    get_lead,
    get_lead_observability,
    get_lead_state,
    lead_to_response,
    list_leads,
    save_agent_runs,
    submit_human_review,
    update_lead_pipeline,
)
from app.schemas import (
    AgentRunObservability,
    EvaluationMetrics,
    ExperimentCompareRequest,
    ExperimentCompareResponse,
    ExperimentRecord,
    GTMStateSnapshot,
    HealthResponse,
    HumanReviewRequest,
    KnowledgeBaseResponse,
    KnowledgeSourceInfo,
    LeadCreate,
    LeadObservabilityResponse,
    LeadResponse,
    LeadsSummaryResponse,
    ToolInfo,
)
from app.tools.knowledge import validate_knowledge_base
from app.tools.registry import list_tools

app = FastAPI(
    title="GTM Agent Factory",
    description="§10–19 — RAG, tools, observability, experimentation, HITL",
    version="5.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    if settings.rag_enabled:
        index_knowledge_base()


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    return HealthResponse(
        status="ok",
        version="5.0.0",
        phase="portfolio-demo",
        persisted=True,
        lead_count=count_leads(db),
    )


@app.get("/api/tools", response_model=List[ToolInfo])
def get_tools():
    """Registered knowledge tools — vision §14."""
    return [ToolInfo(**tool) for tool in list_tools()]


@app.get("/api/knowledge", response_model=KnowledgeBaseResponse)
def get_knowledge_base():
    """Knowledge base inventory — vision §9."""
    raw = validate_knowledge_base()
    rag = get_rag_status()
    return KnowledgeBaseResponse(
        root=raw["root"],
        valid=raw["valid"],
        missing_dirs=raw["missing_dirs"],
        empty_dirs=raw["empty_dirs"],
        total_documents=raw["total_documents"],
        sources=[KnowledgeSourceInfo(**item) for item in raw["sources"]],
        vector_store=rag.get("vector_store", "chromadb"),
        embedding_model=rag.get("embedding_model"),
        indexed_chunks=int(rag.get("indexed_chunks") or 0),
    )


@app.get("/api/evaluation/metrics", response_model=EvaluationMetrics)
def get_evaluation_metrics(db: Session = Depends(get_db)):
    return compute_evaluation_metrics(db)


@app.get("/api/leads/summary", response_model=LeadsSummaryResponse)
def get_leads_summary(db: Session = Depends(get_db)):
    return LeadsSummaryResponse(
        total_leads=count_leads(db),
        persisted=True,
    )


@app.get("/api/leads", response_model=List[LeadResponse])
def get_leads(db: Session = Depends(get_db)):
    return list_leads(db)


@app.get("/api/leads/{lead_id}", response_model=LeadResponse)
def get_lead_by_id(lead_id: int, db: Session = Depends(get_db)):
    lead = get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.get("/api/leads/{lead_id}/state", response_model=GTMStateSnapshot)
def get_lead_state_by_id(lead_id: int, db: Session = Depends(get_db)):
    snapshot = get_lead_state(db, lead_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Shared state not found for lead")
    return snapshot


@app.get("/api/leads/{lead_id}/observability", response_model=LeadObservabilityResponse)
def get_lead_observability_by_id(lead_id: int, db: Session = Depends(get_db)):
    """Agent run observability — vision §18."""
    runs = get_lead_observability(db, lead_id)
    if runs is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadObservabilityResponse(
        lead_id=lead_id,
        runs=[AgentRunObservability(**run) for run in runs],
    )


@app.post("/api/leads/{lead_id}/review", response_model=LeadResponse)
def review_lead(lead_id: int, body: HumanReviewRequest, db: Session = Depends(get_db)):
    """Human-in-the-loop decision — vision §19."""
    lead = submit_human_review(db, lead_id, decision=body.decision, notes=body.notes)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.commit()
    db.refresh(lead)
    response = get_lead(db, lead_id)
    if not response:
        raise HTTPException(status_code=404, detail="Lead not found")
    return response


@app.get("/api/experiments", response_model=List[ExperimentRecord])
def get_experiments(db: Session = Depends(get_db), limit: int = 20):
    """Recent A/B prompt comparisons — vision §15–16."""
    records = list_experiments(db, limit=limit)
    return [
        ExperimentRecord(
            id=record.id,
            lead_id=record.lead_id,
            agent_name=record.agent_name,
            version_a=record.version_a,
            version_b=record.version_b,
            result_a=record.result_a,
            result_b=record.result_b,
            winner=record.winner,
            metrics=record.metrics or {},
            created_at=record.created_at,
        )
        for record in records
    ]


@app.post("/api/experiments/compare", response_model=ExperimentCompareResponse)
def run_experiment_compare(body: ExperimentCompareRequest, db: Session = Depends(get_db)):
    """A/B prompt comparison — vision §15–16."""
    try:
        record = compare_prompt_versions(
            db,
            lead_id=body.lead_id,
            agent_name=body.agent_name,
            version_a=body.version_a,
            version_b=body.version_b,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not record:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.commit()
    return ExperimentCompareResponse(
        id=record.id,
        lead_id=record.lead_id,
        agent_name=record.agent_name,
        version_a=record.version_a,
        version_b=record.version_b,
        result_a=record.result_a,
        result_b=record.result_b,
        winner=record.winner,
        metrics=record.metrics or {},
    )


@app.post("/api/leads/submit", response_model=LeadResponse)
def submit_lead(data: LeadCreate, db: Session = Depends(get_db)):
    lead_data = {
        "company_name": data.company_name,
        "industry": data.industry,
        "company_size": data.company_size,
        "message": data.message,
    }

    lead = create_lead(db, data)

    try:
        pipeline_result = run_pipeline(lead_data)

        if pipeline_result.runs:
            save_agent_runs(db, lead.id, pipeline_result.runs)

        update_lead_pipeline(
            db,
            lead.id,
            status=pipeline_result.status,
            error=pipeline_result.error,
            step_id=pipeline_result.step_id,
            processing_time_ms=pipeline_result.processing_time_ms,
            state_snapshot=pipeline_result.state_snapshot,
        )
        db.commit()
        db.refresh(lead)

        return lead_to_response(
            lead,
            pipeline_results=pipeline_result.results,
            pipeline_status=pipeline_result.status,
            pipeline_error=pipeline_result.error,
            pipeline_step_id=pipeline_result.step_id,
            processing_time_ms=pipeline_result.processing_time_ms,
            state_snapshot=pipeline_result.state_snapshot,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"message": str(e), "failed_step": 0})
