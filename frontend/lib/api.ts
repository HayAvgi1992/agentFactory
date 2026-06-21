const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface PlannerOutput {
  required_sources: string[];
}

export interface ResearchOutput {
  retrieved_documents: string[];
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
  reasoning?: string;
}

export interface ProductFitOutput {
  recommended_product: string;
  alternative_products: string[];
  confidence: number;
  matching_requirements: string[];
  reasoning: string;
}

export interface OutreachOutput {
  email: string;
  linkedin: string;
  questions: string[];
}

export interface RecommendationOutput {
  next_action: string;
}

export interface EvaluationAgentOutput {
  confidence: number;
  needs_human_review: boolean;
  missing_information: string[];
}

export interface AgentResults {
  planner?: PlannerOutput;
  research?: ResearchOutput;
  qualification: QualificationOutput;
  product_fit?: ProductFitOutput;
  outreach: OutreachOutput;
  recommendation: RecommendationOutput;
  evaluation?: EvaluationAgentOutput;
  retrieved_context: RetrievedContextItem[];
  processing_time_ms: number;
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
  results?: AgentResults;
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
  getHealth: () => fetchApi<HealthResponse>("/health"),
  getEvaluationMetrics: () => fetchApi<EvaluationMetrics>("/api/evaluation/metrics"),
  getLeadsSummary: () => fetchApi<LeadsSummary>("/api/leads/summary"),
  getLeads: () => fetchApi<Lead[]>("/api/leads"),
  getLead: (id: number) => fetchApi<Lead>(`/api/leads/${id}`),
  submitLead: (data: Record<string, unknown>) =>
    fetchApi<Lead>("/api/leads/submit", { method: "POST", body: JSON.stringify(data) }),
};

/** Must match backend settings.step_delay_sec (default 2s) */
export const PIPELINE_STEP_MS = 2000;
