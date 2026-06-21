"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Lead, LeadObservabilityResponse } from "@/lib/api";

interface ObservabilityPanelProps {
  lead: Lead;
}

export function ObservabilityPanel({ lead }: ObservabilityPanelProps) {
  const [data, setData] = useState<LeadObservabilityResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await api.getLeadObservability(lead.id));
    } catch {
      setError("Observability data unavailable for this lead.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [lead.id]);

  useEffect(() => {
    load();
  }, [load]);

  const totalTokens = data?.runs.reduce((sum, run) => sum + (run.token_usage ?? 0), 0) ?? 0;

  return (
    <div className="observability-panel">
      <div className="section-header">
        <h2>Agent Observability</h2>
        <button type="button" className="btn-secondary" onClick={load} disabled={loading}>
          {loading ? "Loading…" : "Refresh"}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {data && (
        <>
          {totalTokens > 0 && (
            <p className="meta">Estimated total tokens this pipeline: {totalTokens.toLocaleString()}</p>
          )}
          <table className="dashboard-table observability-table">
            <thead>
              <tr>
                <th>Agent</th>
                <th>Prompt</th>
                <th>Tools</th>
                <th>Docs</th>
                <th>Latency</th>
                <th>Tokens</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {data.runs.map((run) => (
                <tr key={run.id}>
                  <td>{run.agent_name}</td>
                  <td>{run.prompt_version ?? "—"}</td>
                  <td>{run.tools_used?.length ? run.tools_used.join(", ") : "—"}</td>
                  <td>{run.retrieved_documents?.length ?? 0}</td>
                  <td>{run.latency_ms != null ? `${run.latency_ms}ms` : "—"}</td>
                  <td>{run.token_usage != null ? run.token_usage.toLocaleString() : "—"}</td>
                  <td>
                    {run.confidence != null ? `${Math.round(run.confidence * 100)}%` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
