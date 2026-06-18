"use client";

import { Badge } from "./Card";
import type { Lead } from "@/lib/api";
import { ACTION_LABELS, formatDate } from "@/lib/utils";

interface LeadPipelineProps {
  lead: Lead;
}

export function LeadPipeline({ lead }: LeadPipelineProps) {
  const results = lead.results;
  if (!results) {
    return <p className="empty">No results yet.</p>;
  }

  const { qualification, outreach, recommendation } = results;
  const action = ACTION_LABELS[recommendation.next_action];

  return (
    <div className="pipeline">
      <div className="pipeline-header">
        <div>
          <h3>{lead.company_name}</h3>
          <p className="meta">
            {lead.industry && `${lead.industry} · `}
            {lead.company_size && `${lead.company_size} employees · `}
            {formatDate(lead.created_at)}
          </p>
        </div>
        {action && (
          <span
            className="action-badge"
            style={{
              background: action.color,
              color: action.textColor ?? "#fff",
            }}
          >
            {action.label}
          </span>
        )}
      </div>

      <div className="pipeline-steps">
        <Step number={1} title="Qualification Agent">
          <div className="score-row">
            <span className="score">{qualification.score}/100</span>
            <Badge variant={qualification.qualified ? "success" : "danger"}>
              {qualification.qualified ? "Qualified" : "Not Qualified"}
            </Badge>
          </div>
          <p>{qualification.reason}</p>
        </Step>

        <Step number={2} title="Outreach Agent">
          <details>
            <summary>Email</summary>
            <pre>{outreach.email}</pre>
          </details>
          <details>
            <summary>LinkedIn Message</summary>
            <p>{outreach.linkedin}</p>
          </details>
          <details open>
            <summary>Discovery Questions</summary>
            <ol>
              {outreach.questions.map((q, i) => (
                <li key={i}>{q}</li>
              ))}
            </ol>
          </details>
        </Step>

        <Step number={3} title="Recommendation Agent">
          <p>
            Next action: <strong>{recommendation.next_action}</strong>
          </p>
        </Step>
      </div>

      <p className="processing-time">Completed in {results.processing_time_ms}ms</p>
    </div>
  );
}

function Step({
  number,
  title,
  children,
}: {
  number: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="pipeline-step">
      <div className="step-indicator">
        <span className="step-number">{number}</span>
        <span className="step-title">{title}</span>
      </div>
      <div className="step-content">{children}</div>
    </div>
  );
}
