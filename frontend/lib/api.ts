const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface PlannerOutput {
  required_sources: string[];
  reasoning?: string;
  patterns?: string[];
  context_inputs?: string[];
  prompt_version?: string;
}

export interface ResearchOutput {
  retrieved_documents: string[];
  reasoning?: string;
  patterns_identified?: string[];
  tools_used?: string[];
  retrieval_methods?: string[];
  prompt_version?: string;
}

export interface RetrievedContextItem {
  source: string;
  document_id: string;
  title: string;
  snippet: string;
}

export interface QualificationOutput {
  qualified: boolean;
  score: number;
  reason: string;
  signals: string[];
  risks: string[];
  patterns?: string[];
  tradeoffs?: string[];
  reasoning?: string;
  context_inputs?: string[];
}

export interface ProductFitOutput {
  recommended_product: string;
  alternative_products: string[];
  confidence: number;
  matching_requirements: string[];
  reasoning: string;
  patterns?: string[];
  tradeoffs?: string[];
  context_inputs?: string[];
}

export interface OutreachOutput {
  email: string;
  linkedin: string;
  questions: string[];
  reasoning?: string;
  patterns?: string[];
}

export interface RecommendationOutput {
  next_action: string;
  reasoning?: string;
  patterns?: string[];
  tradeoffs?: string[];
}

export interface EvaluationAgentOutput {
  confidence: number;
  needs_human_review: boolean;
  missing_information: string[];
  reasoning?: string;
  context_inputs?: string[];
  prompt_version?: string;
}

export interface AgentResults {
  planner?: PlannerOutput;
  research?: ResearchOutput;
  qualification: QualificationOutput;
  product_fit?: ProductFitOutput;
  outreach?: OutreachOutput;
  recommendation?: RecommendationOutput;
  evaluation?: EvaluationAgentOutput;
  retrieved_context: RetrievedContextItem[];
  processing_time_ms: number;
}

export interface GTMStateSnapshot {
  lead: Record<string, unknown>;
  planner?: Record<string, unknown> | null;
  research?: Record<string, unknown> | null;
  retrieved_context: RetrievedContextItem[];
  qualification?: Record<string, unknown> | null;
  product_fit?: Record<string, unknown> | null;
  outreach?: Record<string, unknown> | null;
  recommendation?: Record<string, unknown> | null;
  evaluation?: Record<string, unknown> | null;
  populated_fields: string[];
}

export interface Lead {
  id: number;
  company_name: string;
  industry?: string;
  company_size?: string;
  message: string;
  created_at: string;
  pipeline_status: "pending" | "complete" | "partial";
  pipeline_error?: string | null;
  pipeline_step_id?: string | null;
  processing_time_ms?: number | null;
  human_review_status?: string | null;
  human_review_notes?: string | null;
  results?: AgentResults;
  state_snapshot?: GTMStateSnapshot | null;
}

export interface EvaluationMetrics {
  total_leads: number;
  qualified_leads: number;
  qualification_rate: number;
  meeting_recommendations: number;
  meeting_recommendation_rate: number;
  average_score: number | null;
  processed_leads: number;
  average_confidence: number | null;
  human_review_count: number;
  human_review_rate: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  phase: string;
  persisted: boolean;
  lead_count: number;
}

export interface KnowledgeSourceInfo {
  source: string;
  label: string;
  simulates: string;
  description: string;
  path: string;
  document_count: number;
  documents: string[];
}

export interface KnowledgeBaseResponse {
  root: string;
  valid: boolean;
  missing_dirs: string[];
  empty_dirs: string[];
  total_documents: number;
  sources: KnowledgeSourceInfo[];
  vector_store?: string;
  embedding_model?: string | null;
  indexed_chunks?: number;
}

export interface AgentRunObservability {
  id: number;
  agent_name: string;
  prompt_version?: string | null;
  tools_used?: string[];
  retrieved_documents?: string[];
  confidence?: number | null;
  latency_ms?: number | null;
  token_usage?: number | null;
}

export interface LeadObservabilityResponse {
  lead_id: number;
  runs: AgentRunObservability[];
}

export interface ExperimentCompareResponse {
  id: number;
  lead_id: number;
  agent_name: string;
  version_a: string;
  version_b: string;
  result_a: Record<string, unknown>;
  result_b: Record<string, unknown>;
  winner?: string | null;
  metrics: Record<string, unknown>;
}

export interface ExperimentRecord extends ExperimentCompareResponse {
  created_at: string;
}

export interface ExperimentCompareRequest {
  lead_id: number;
  agent_name?: string;
  version_a?: string;
  version_b?: string;
}

export interface ToolInfo {
  name: string;
  description: string;
  source: string;
}

export interface LeadsSummary {
  total_leads: number;
  persisted: boolean;
}

export class ApiError extends Error {
  failedStep?: number;

  constructor(message: string, failedStep?: number) {
    super(message);
    this.name = "ApiError";
    this.failedStep = failedStep;
  }
}

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail;
    if (detail && typeof detail === "object" && "message" in detail) {
      throw new ApiError(detail.message, detail.failed_step);
    }
    const message = typeof detail === "string" ? detail : "API error";
    throw new ApiError(message);
  }
  return res.json();
}

export const api = {
  getKnowledgeBase: () => fetchApi<KnowledgeBaseResponse>("/api/knowledge"),
  getTools: () => fetchApi<ToolInfo[]>("/api/tools"),
  getLeadObservability: (id: number) =>
    fetchApi<LeadObservabilityResponse>(`/api/leads/${id}/observability`),
  getExperiments: () => fetchApi<ExperimentRecord[]>("/api/experiments"),
  runExperimentCompare: (body: ExperimentCompareRequest) =>
    fetchApi<ExperimentCompareResponse>("/api/experiments/compare", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  submitHumanReview: (id: number, decision: "approve" | "reject", notes?: string) =>
    fetchApi<Lead>(`/api/leads/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ decision, notes }),
    }),
  getHealth: () => fetchApi<HealthResponse>("/health"),
  getEvaluationMetrics: () => fetchApi<EvaluationMetrics>("/api/evaluation/metrics"),
  getLeadsSummary: () => fetchApi<LeadsSummary>("/api/leads/summary"),
  getLeads: () => fetchApi<Lead[]>("/api/leads"),
  getLead: (id: number) => fetchApi<Lead>(`/api/leads/${id}`),
  getLeadState: (id: number) => fetchApi<GTMStateSnapshot>(`/api/leads/${id}/state`),
  submitLead: (data: Record<string, unknown>) =>
    fetchApi<Lead>("/api/leads/submit", { method: "POST", body: JSON.stringify(data) }),
};

/** Must match backend settings.step_delay_sec (default 2s) */
export const PIPELINE_STEP_MS = 2000;
