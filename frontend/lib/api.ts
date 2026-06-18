const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface QualificationOutput {
  qualified: boolean;
  score: number;
  reason: string;
}

export interface OutreachOutput {
  email: string;
  linkedin: string;
  questions: string[];
}

export interface RecommendationOutput {
  next_action: string;
}

export interface AgentResults {
  qualification: QualificationOutput;
  outreach: OutreachOutput;
  recommendation: RecommendationOutput;
  processing_time_ms: number;
}

export interface Lead {
  id: number;
  company_name: string;
  industry?: string;
  company_size?: string;
  message: string;
  created_at: string;
  results?: AgentResults;
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
  getLeads: () => fetchApi<Lead[]>("/api/leads"),
  getLead: (id: number) => fetchApi<Lead>(`/api/leads/${id}`),
  submitLead: (data: Record<string, unknown>) =>
    fetchApi<Lead>("/api/leads/submit", { method: "POST", body: JSON.stringify(data) }),
};

/** Must match backend settings.step_delay_sec (default 2s) */
export const PIPELINE_STEP_MS = 2000;
