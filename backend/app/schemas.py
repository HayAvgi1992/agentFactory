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


class EvaluationMetrics(BaseModel):
    total_leads: int
    qualified_leads: int
    qualification_rate: float
    meeting_recommendations: int
    meeting_recommendation_rate: float
    average_score: Optional[float] = None
    processed_leads: int


class HealthResponse(BaseModel):
    status: str
    version: str = "3.0.0"
    phase: str = "3-evaluation"
    persisted: bool = True
    lead_count: int = 0


class LeadsSummaryResponse(BaseModel):
    total_leads: int
    persisted: bool = True
