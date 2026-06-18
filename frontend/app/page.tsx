"use client";

import { useCallback, useEffect, useState } from "react";
import { Card } from "@/components/Card";
import { LeadForm } from "@/components/LeadForm";
import { LeadPipeline } from "@/components/LeadPipeline";
import { PipelineDiagram } from "@/components/PipelineDiagram";
import { api } from "@/lib/api";
import type { Lead } from "@/lib/api";
import { ACTION_LABELS } from "@/lib/utils";

export default function HomePage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [failedStep, setFailedStep] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    try {
      const leadsData = await api.getLeads();
      setLeads(leadsData);
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

      <Card title="MVP Dashboard">
        {leads.length === 0 ? (
          <p className="empty">No leads yet. Submit one above.</p>
        ) : (
          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Lead</th>
                  <th>Score</th>
                  <th>Qualification</th>
                  <th>Recommendation</th>
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
