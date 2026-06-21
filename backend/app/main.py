from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db, init_db
from app.evaluation import compute_evaluation_metrics
from app.pipeline import run_pipeline
from app.repository import (
    count_leads,
    create_lead,
    get_lead,
    lead_to_response,
    list_leads,
    save_agent_runs,
    update_lead_pipeline,
)
from app.schemas import (
    EvaluationMetrics,
    HealthResponse,
    LeadCreate,
    LeadResponse,
    LeadsSummaryResponse,
)

app = FastAPI(
    title="GTM Agent Factory",
    description="Phase 4 — 7-agent target architecture with shared GTMState",
    version="4.0.0",
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


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    return HealthResponse(
        status="ok",
        version="4.0.0",
        phase="4-target-architecture",
        persisted=True,
        lead_count=count_leads(db),
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
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"message": str(e), "failed_step": 0})
