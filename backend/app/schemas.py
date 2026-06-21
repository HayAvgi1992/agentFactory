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
    reasoning: str = ""
    patterns: List[str] = []


class ResearchOutput(BaseModel):
    retrieved_documents: List[str]
    reasoning: str = ""
    patterns_identified: List[str] = []


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
    patterns: List[str] = []
    tradeoffs: List[str] = []
    reasoning: Optional[str] = None
    context_inputs: List[str] = []


class ProductFitOutput(BaseModel):
    recommended_product: str
    alternative_products: List[str] = []
    confidence: float
    matching_requirements: List[str] = []
    reasoning: str
    patterns: List[str] = []
    tradeoffs: List[str] = []
    context_inputs: List[str] = []


class KnowledgeSourceInfo(BaseModel):
    source: str
    label: str
    simulates: str
    description: str
    path: str
    document_count: int
    documents: List[str]


class KnowledgeBaseResponse(BaseModel):
    root: str
    valid: bool
    missing_dirs: List[str] = []
    empty_dirs: List[str] = []
    total_documents: int
    sources: List[KnowledgeSourceInfo]


class OutreachOutput(BaseModel):
    email: str
    linkedin: str
    questions: List[str]
    reasoning: str = ""
    patterns: List[str] = []


class RecommendationOutput(BaseModel):
    next_action: str
    reasoning: str = ""
    patterns: List[str] = []
    tradeoffs: List[str] = []


class EvaluationAgentOutput(BaseModel):
    confidence: float
    needs_human_review: bool
    missing_information: List[str] = []
    reasoning: str = ""


class AgentResults(BaseModel):
    planner: Optional[PlannerOutput] = None
    research: Optional[ResearchOutput] = None
    qualification: QualificationOutput
    product_fit: Optional[ProductFitOutput] = None
    outreach: Optional[OutreachOutput] = None
    recommendation: Optional[RecommendationOutput] = None
    evaluation: Optional[EvaluationAgentOutput] = None
    retrieved_context: List[RetrievedContextItem] = []
    processing_time_ms: int


class GTMStateSnapshot(BaseModel):
    """Public view of shared LangGraph state (vision §5)."""

    lead: Dict[str, Any]
    planner: Optional[Dict[str, Any]] = None
    research: Optional[Dict[str, Any]] = None
    retrieved_context: List[RetrievedContextItem] = []
    qualification: Optional[Dict[str, Any]] = None
    product_fit: Optional[Dict[str, Any]] = None
    outreach: Optional[Dict[str, Any]] = None
    recommendation: Optional[Dict[str, Any]] = None
    evaluation: Optional[Dict[str, Any]] = None
    populated_fields: List[str] = []


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
    state_snapshot: Optional[GTMStateSnapshot] = None


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
    phase: str = "8-product-fit-knowledge"
    persisted: bool = True
    lead_count: int = 0


class LeadsSummaryResponse(BaseModel):
    total_leads: int
    persisted: bool = True
