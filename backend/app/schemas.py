from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel

PipelineStatus = Literal["pending", "complete", "partial"]


class AgentRunRecord(BaseModel):
    agent_name: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    prompt_version: Optional[str] = None
    tools_used: List[str] = []
    retrieved_documents: List[str] = []
    confidence: Optional[float] = None
    latency_ms: Optional[int] = None
    token_usage: Optional[int] = None


class LeadCreate(BaseModel):
    company_name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    message: str


class PlannerOutput(BaseModel):
    required_sources: List[str]
    reasoning: str = ""
    patterns: List[str] = []
    context_inputs: List[str] = []
    prompt_version: Optional[str] = None


class ResearchOutput(BaseModel):
    retrieved_documents: List[str]
    reasoning: str = ""
    patterns_identified: List[str] = []
    tools_used: List[str] = []
    retrieval_methods: List[str] = []
    prompt_version: Optional[str] = None


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
    vector_store: str = "chromadb"
    embedding_model: Optional[str] = None
    indexed_chunks: int = 0


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
    context_inputs: List[str] = []
    prompt_version: Optional[str] = None


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
    human_review_status: Optional[str] = None
    human_review_notes: Optional[str] = None
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
    phase: str = "10-19-rag-tools-observability"
    persisted: bool = True
    lead_count: int = 0


class LeadsSummaryResponse(BaseModel):
    total_leads: int
    persisted: bool = True


class ToolInfo(BaseModel):
    name: str
    description: str
    source: str


class AgentRunObservability(BaseModel):
    id: int
    agent_name: str
    prompt_version: Optional[str] = None
    tools_used: List[str] = []
    retrieved_documents: List[str] = []
    confidence: Optional[float] = None
    latency_ms: Optional[int] = None
    token_usage: Optional[int] = None


class LeadObservabilityResponse(BaseModel):
    lead_id: int
    runs: List[AgentRunObservability]


class ExperimentSummary(BaseModel):
    id: int
    lead_id: int
    agent_name: str
    version_a: str
    version_b: str
    winner: Optional[str] = None
    metrics: Dict[str, Any] = {}
    created_at: datetime


class ExperimentCompareRequest(BaseModel):
    lead_id: int
    agent_name: str = "qualification"
    version_a: str = "v1"
    version_b: str = "v2"


class ExperimentCompareResponse(BaseModel):
    id: int
    lead_id: int
    agent_name: str
    version_a: str
    version_b: str
    result_a: Dict[str, Any]
    result_b: Dict[str, Any]
    winner: Optional[str] = None
    metrics: Dict[str, Any] = {}


class ExperimentRecord(ExperimentCompareResponse):
    created_at: datetime


class HumanReviewRequest(BaseModel):
    decision: Literal["approve", "reject"]
    notes: Optional[str] = None
