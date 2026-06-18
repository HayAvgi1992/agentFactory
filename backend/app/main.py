from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.pipeline import PipelineStepError, run_pipeline
from app.schemas import HealthResponse, LeadCreate, LeadResponse
from app.store import create_and_store_lead, get_lead, list_leads

app = FastAPI(
    title="GTM Agent Factory",
    description="Phase 1 MVP — AI SDR workflow with Qualification, Outreach, and Recommendation agents",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


@app.get("/api/leads", response_model=List[LeadResponse])
def get_leads():
    return list_leads()


@app.get("/api/leads/{lead_id}", response_model=LeadResponse)
def get_lead_by_id(lead_id: int):
    lead = get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.post("/api/leads/submit", response_model=LeadResponse)
def submit_lead(data: LeadCreate):
    lead_data = {
        "company_name": data.company_name,
        "industry": data.industry,
        "company_size": data.company_size,
        "message": data.message,
    }
    try:
        results = run_pipeline(lead_data)
        return create_and_store_lead(data, results)
    except PipelineStepError as e:
        raise HTTPException(
            status_code=500,
            detail={"message": e.message, "failed_step": e.step_index, "step_id": e.step_id},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": str(e), "failed_step": 0})
