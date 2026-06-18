from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class LeadCreate(BaseModel):
    company_name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    message: str


class QualificationOutput(BaseModel):
    qualified: bool
    score: int
    reason: str


class OutreachOutput(BaseModel):
    email: str
    linkedin: str
    questions: List[str]


class RecommendationOutput(BaseModel):
    next_action: str


class AgentResults(BaseModel):
    qualification: QualificationOutput
    outreach: OutreachOutput
    recommendation: RecommendationOutput
    processing_time_ms: int


class LeadResponse(BaseModel):
    id: int
    company_name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    message: str
    created_at: datetime
    results: Optional[AgentResults] = None


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    phase: str = "1-mvp"
