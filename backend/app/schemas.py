from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel

PipelineStatus = Literal["pending", "complete", "partial"]


class AgentRunRecord(BaseModel):
    agent_name: str
    input: Dict[str, Any]
    output: Dict[str, Any]


class LeadCreate(BaseModel):
    company_name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    message: str


class PlannerOutput(BaseModel):
    required_sources: List[str]


class ResearchOutput(BaseModel):
    retrieved_documents: List[str]


class RetrievedContextItem(BaseModel):
    source: str
    document_id: str
    title: str
    snippet: str


class QualificationOutput(BaseModel):
    qualified: bool
    score: int
    reason: str
    signals: List[str] = []
    risks: List[str] = []
    reasoning: Optional[str] = None


class ProductFitOutput(BaseModel):
    recommended_product: str
    alternative_products: List[str] = []
    confidence: float
    matching_requirements: List[str] = []
    reasoning: str


class OutreachOutput(BaseModel):
    email: str
    linkedin: str
    questions: List[str]


class RecommendationOutput(BaseModel):
    next_action: str


class EvaluationAgentOutput(BaseModel):
    confidence: float
    needs_human_review: bool
    missing_information: List[str] = []


class AgentResults(BaseModel):
    planner: Optional[PlannerOutput] = None
    research: Optional[ResearchOutput] = None
    qualification: QualificationOutput
    product_fit: Optional[ProductFitOutput] = None
    outreach: OutreachOutput
    recommendation: RecommendationOutput
    evaluation: Optional[EvaluationAgentOutput] = None
    retrieved_context: List[RetrievedContextItem] = []
    processing_time_ms: int


class LeadResponse(BaseModel):
    id: int
    company_name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    message: str
    created_at: datetime
    pipeline_status: PipelineStatus = "pending"
    pipeline_error: Optional[str] = None
    pipeline_step_id: Optional[str] = None
    processing_time_ms: Optional[int] = None
    results: Optional[AgentResults] = None


class EvaluationMetrics(BaseModel):
    total_leads: int
    qualified_leads: int
    qualification_rate: float
    meeting_recommendations: int
    meeting_recommendation_rate: float
    average_score: Optional[float] = None
    processed_leads: int
    average_confidence: Optional[float] = None
    human_review_count: int = 0
    human_review_rate: float = 0.0


class HealthResponse(BaseModel):
    status: str
    version: str = "4.0.0"
    phase: str = "4-target-architecture"
    persisted: bool = True
    lead_count: int = 0


class LeadsSummaryResponse(BaseModel):
    total_leads: int
    persisted: bool = True
