"use client";

import { useCallback, useEffect, useState } from "react";
import { Card } from "@/components/Card";
import { EvaluationMetricsPanel } from "@/components/EvaluationMetrics";
import { LeadForm } from "@/components/LeadForm";
import { LeadPipeline } from "@/components/LeadPipeline";
import { PipelineDiagram } from "@/components/PipelineDiagram";
import { api } from "@/lib/api";
import type { EvaluationMetrics, Lead } from "@/lib/api";
import { ACTION_LABELS } from "@/lib/utils";

export default function HomePage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [failedStep, setFailedStep] = useState<number | null>(null);

  const [persistedCount, setPersistedCount] = useState<number | null>(null);
  const [metrics, setMetrics] = useState<EvaluationMetrics | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [leadsData, summary, metricsData] = await Promise.all([
        api.getLeads(),
        api.getLeadsSummary(),
        api.getEvaluationMetrics(),
      ]);
      setLeads(leadsData);
      setPersistedCount(summary.total_leads);
      setMetrics(metricsData);
      if (leadsData.length > 0 && !selectedLead) {
        setSelectedLead(leadsData[0]);
      }
    } catch {
      // Backend may not be running yet
    }
  }, [selectedLead]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handlePipelineStart = () => {
    setFailedStep(null);
  };

  const handlePipelineFailure = (step: number) => {
    setFailedStep(step);
  };

  const handleLeadSubmitted = (lead: Lead) => {
    setFailedStep(null);
    setLeads((prev) => [lead, ...prev]);
    setSelectedLead(lead);
    refresh();
  };

  return (
    <div className="page">
      <div className="grid-2">
        <Card title="Submit Lead">
          <LeadForm
            onSubmitted={handleLeadSubmitted}
            onProcessingChange={setIsProcessing}
            onPipelineStart={handlePipelineStart}
            onPipelineFailure={handlePipelineFailure}
          />
        </Card>

        <Card title="Agent Pipeline">
          <PipelineDiagram
            activeLead={selectedLead}
            isProcessing={isProcessing}
            failedStep={failedStep}
          />
        </Card>
      </div>

      <EvaluationMetricsPanel metrics={metrics} />

      <Card
        title="MVP Dashboard"
        action={
          persistedCount !== null ? (
            <span className="dashboard-persisted" title="Loaded from SQLite on the backend">
              {persistedCount} stored · survives refresh
            </span>
          ) : undefined
        }
      >
        {leads.length === 0 ? (
          <p className="empty">No leads yet. Submit one above.</p>
        ) : (
          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Lead</th>
                  <th>Score</th>
                  <th>Product</th>
                  <th>Qualification</th>
                  <th>Recommendation</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((lead) => {
                  const r = lead.results;
                  const action = r
                    ? ACTION_LABELS[r.recommendation.next_action]
                    : null;
                  return (
                    <tr
                      key={lead.id}
                      className={selectedLead?.id === lead.id ? "active" : ""}
                      onClick={() => setSelectedLead(lead)}
                    >
                      <td>
                        <strong>{lead.company_name}</strong>
                        {lead.industry && (
                          <span className="cell-sub">{lead.industry}</span>
                        )}
                      </td>
                      <td>{r ? `${r.qualification.score}/100` : "—"}</td>
                      <td>{r?.product_fit?.recommended_product ?? "—"}</td>
                      <td>
                        {r ? (
                          <span
                            className={`qual-badge ${
                              r.qualification.qualified ? "yes" : "no"
                            }`}
                          >
                            {r.qualification.qualified ? "Qualified" : "Not Qualified"}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>
                        {action ? (
                          <span
                            className="action-tag"
                            style={{
                              background: action.color,
                              color: action.textColor ?? "#fff",
                            }}
                          >
                            {action.label}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>
                        {r?.evaluation
                          ? `${Math.round(r.evaluation.confidence * 100)}%`
                          : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {selectedLead && (
        <Card title="Lead Details">
          <LeadPipeline lead={selectedLead} />
        </Card>
      )}
    </div>
  );
}
