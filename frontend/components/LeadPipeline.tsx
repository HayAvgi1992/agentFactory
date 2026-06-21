"use client";

import { ReasoningBlock } from "@/components/ReasoningBlock";
import { SharedStatePanel } from "@/components/SharedStatePanel";
import { Badge } from "./Card";
import type { Lead } from "@/lib/api";
import { ACTION_LABELS, formatDate } from "@/lib/utils";

interface LeadPipelineProps {
  lead: Lead;
}

export function LeadPipeline({ lead }: LeadPipelineProps) {
  const results = lead.results;
  if (!results && !lead.state_snapshot) {
    return <p className="empty">No results yet.</p>;
  }

  if (!results) {
    return (
      <div className="pipeline">
        <div className="pipeline-header">
          <div>
            <h3>{lead.company_name}</h3>
            <p className="meta">Pipeline partial — shared state only</p>
          </div>
        </div>
        <SharedStatePanel snapshot={lead.state_snapshot} />
      </div>
    );
  }

  const {
    planner,
    research,
    qualification,
    product_fit,
    outreach,
    recommendation,
    evaluation,
    retrieved_context,
  } = results;
  const action = recommendation
    ? ACTION_LABELS[recommendation.next_action]
    : null;
  let stepNumber = 0;

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
        {planner && (
          <Step number={++stepNumber} title="Planner Agent">
            <p>
              Required sources:{" "}
              <strong>{planner.required_sources.join(", ")}</strong>
            </p>
            {planner.context_inputs && planner.context_inputs.length > 0 && (
              <p className="context-inputs">
                <strong>Inputs:</strong> {planner.context_inputs.join(" · ")}
              </p>
            )}
            <ReasoningBlock
              reasoning={planner.reasoning}
              patterns={planner.patterns}
            />
          </Step>
        )}

        {research && (
          <Step number={++stepNumber} title="Research Agent">
            <p>
              Retrieved documents:{" "}
              <strong>
                {research.retrieved_documents.length > 0
                  ? research.retrieved_documents.join(", ")
                  : "none"}
              </strong>
            </p>
            {research.tools_used && research.tools_used.length > 0 && (
              <p className="context-inputs">
                <strong>Tools:</strong> {research.tools_used.join(" · ")}
                {research.retrieval_methods && research.retrieval_methods.length > 0 && (
                  <> · <strong>Methods:</strong> {research.retrieval_methods.join(", ")}</>
                )}
              </p>
            )}
            <ReasoningBlock
              reasoning={research.reasoning}
              patterns={research.patterns_identified}
            />
            {retrieved_context.length > 0 && (
              <details open>
                <summary>Context snippets ({retrieved_context.length})</summary>
                <ul className="context-list">
                  {retrieved_context.map((item, i) => (
                    <li key={i}>
                      <strong>[{item.source}] {item.title}</strong>
                      <p>{item.snippet}</p>
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </Step>
        )}

        <Step number={++stepNumber} title="Qualification Agent">
          <div className="score-row">
            <span className="score">{qualification.score}/100</span>
            <Badge variant={qualification.qualified ? "success" : "danger"}>
              {qualification.qualified ? "Qualified" : "Not Qualified"}
            </Badge>
          </div>
          {qualification.context_inputs && qualification.context_inputs.length > 0 && (
            <p className="context-inputs">
              <strong>Inputs:</strong> {qualification.context_inputs.join(" · ")}
            </p>
          )}
          <ReasoningBlock
            reasoning={qualification.reasoning || qualification.reason}
            patterns={qualification.patterns}
            tradeoffs={qualification.tradeoffs}
            extra={
              <>
                {qualification.signals.length > 0 && (
                  <p>
                    <strong>Signals:</strong> {qualification.signals.join(" · ")}
                  </p>
                )}
                {qualification.risks.length > 0 && (
                  <p>
                    <strong>Risks:</strong> {qualification.risks.join(" · ")}
                  </p>
                )}
              </>
            }
          />
        </Step>

        {product_fit && (
          <Step number={++stepNumber} title="Product Fit Agent">
            <p>
              Recommended: <strong>{product_fit.recommended_product}</strong>{" "}
              ({Math.round(product_fit.confidence * 100)}% confidence)
            </p>
            {product_fit.context_inputs && product_fit.context_inputs.length > 0 && (
              <p className="context-inputs">
                <strong>Inputs:</strong> {product_fit.context_inputs.join(" · ")}
              </p>
            )}
            <ReasoningBlock
              reasoning={product_fit.reasoning}
              patterns={product_fit.patterns}
              tradeoffs={product_fit.tradeoffs}
              extra={
                product_fit.matching_requirements.length > 0 ? (
                  <p>
                    <strong>Requirements:</strong>{" "}
                    {product_fit.matching_requirements.join(" · ")}
                  </p>
                ) : undefined
              }
            />
          </Step>
        )}

        {outreach && (
          <Step number={++stepNumber} title="Outreach Agent">
            <ReasoningBlock
              reasoning={outreach.reasoning}
              patterns={outreach.patterns}
            />
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
        )}

        {recommendation && (
          <Step number={++stepNumber} title="Recommendation Agent">
            <p>
              Next action: <strong>{recommendation.next_action}</strong>
            </p>
            <ReasoningBlock
              reasoning={recommendation.reasoning}
              patterns={recommendation.patterns}
              tradeoffs={recommendation.tradeoffs}
            />
          </Step>
        )}

        {evaluation && (
          <Step number={++stepNumber} title="Evaluation Agent">
            <div className="score-row">
              <span className="score">
                {Math.round(evaluation.confidence * 100)}% confidence
              </span>
              <Badge variant={evaluation.needs_human_review ? "danger" : "success"}>
                {evaluation.needs_human_review ? "Needs Review" : "Auto-approved"}
              </Badge>
            </div>
            <ReasoningBlock
              reasoning={evaluation.reasoning}
              extra={
                <>
                  {evaluation.context_inputs && evaluation.context_inputs.length > 0 && (
                    <p>
                      <strong>Inputs:</strong> {evaluation.context_inputs.join(" · ")}
                    </p>
                  )}
                  {evaluation.missing_information.length > 0 ? (
                    <p>
                      <strong>Missing:</strong>{" "}
                      {evaluation.missing_information.join(", ")}
                    </p>
                  ) : undefined}
                </>
              }
            />
          </Step>
        )}
      </div>

      <p className="processing-time">
        Completed in{" "}
        {lead.processing_time_ms ?? results.processing_time_ms}ms
        {lead.pipeline_status === "partial" && lead.pipeline_error && (
          <> · Partial: {lead.pipeline_error}</>
        )}
      </p>

      <SharedStatePanel snapshot={lead.state_snapshot} />
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
