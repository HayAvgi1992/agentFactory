"use client";

import type { GTMStateSnapshot } from "@/lib/api";

const SLICE_LABELS: Record<string, string> = {
  lead: "Lead Input",
  planner: "Planner",
  research: "Research",
  retrieved_context: "Retrieved Context",
  qualification: "Qualification",
  product_fit: "Product Fit",
  outreach: "Outreach",
  recommendation: "Recommendation",
  evaluation: "Evaluation",
};

interface SharedStatePanelProps {
  snapshot?: GTMStateSnapshot | null;
}

export function SharedStatePanel({ snapshot }: SharedStatePanelProps) {
  if (!snapshot) {
    return (
      <p className="empty">
        Shared state unavailable — run the pipeline or reload after submit.
      </p>
    );
  }

  const fields = snapshot.populated_fields.length
    ? snapshot.populated_fields
    : ["lead"];

  return (
    <div className="shared-state">
      <p className="shared-state-intro">
        LangGraph shared state — {snapshot.populated_fields.length} populated slice
        {snapshot.populated_fields.length === 1 ? "" : "s"}
      </p>

      <div className="shared-state-grid">
        {fields.map((field) => (
          <div key={field} className="shared-state-slice">
            <h4>{SLICE_LABELS[field] ?? field}</h4>
            <pre>{formatSlice(field, snapshot)}</pre>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatSlice(field: string, snapshot: GTMStateSnapshot): string {
  const value = snapshot[field as keyof GTMStateSnapshot];
  if (field === "retrieved_context" && Array.isArray(value)) {
    return JSON.stringify(
      value.map((item) => ({
        source: item.source,
        document_id: item.document_id,
        title: item.title,
      })),
      null,
      2,
    );
  }
  return JSON.stringify(value, null, 2);
}
