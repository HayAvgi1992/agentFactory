"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ExperimentRecord, ExperimentCompareResponse, Lead } from "@/lib/api";

interface ExperimentPanelProps {
  lead: Lead;
}

function winnerLabel(winner: string | null | undefined, versionA: string, versionB: string) {
  if (winner === "version_a") return versionA;
  if (winner === "version_b") return versionB;
  if (winner === "tie") return "Tie";
  return "—";
}

function VariantColumn({
  label,
  result,
  isWinner,
}: {
  label: string;
  result: Record<string, unknown>;
  isWinner: boolean;
}) {
  const qualified = Boolean(result.qualified);
  const score = typeof result.score === "number" ? result.score : "—";
  return (
    <div className={`strategy-column${isWinner ? " winner-column" : ""}`}>
      <h4>
        {label}
        {isWinner && <span className="winner"> · Winner</span>}
      </h4>
      <div className="metric-row">
        <span>Qualified</span>
        <span className={qualified ? "winner" : ""}>{qualified ? "Yes" : "No"}</span>
      </div>
      <div className="metric-row">
        <span>Score</span>
        <strong>{score}/100</strong>
      </div>
      {typeof result.reason === "string" && result.reason && (
        <p className="meta">{result.reason}</p>
      )}
    </div>
  );
}

function ExperimentResult({ display }: { display: ExperimentCompareResponse }) {
  return (
    <>
      <p className="lead-count">
        Winner:{" "}
        <strong className="winner">
          {winnerLabel(display.winner, display.version_a, display.version_b)}
        </strong>
      </p>
      <div className="experiment-comparison">
        <VariantColumn
          label={display.version_a}
          result={display.result_a}
          isWinner={display.winner === "version_a"}
        />
        <div className="vs-divider">vs</div>
        <VariantColumn
          label={display.version_b}
          result={display.result_b}
          isWinner={display.winner === "version_b"}
        />
      </div>
    </>
  );
}

export function ExperimentPanel({ lead }: ExperimentPanelProps) {
  const [history, setHistory] = useState<ExperimentRecord[]>([]);
  const [latest, setLatest] = useState<ExperimentCompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadHistory = useCallback(async () => {
    try {
      const rows = await api.getExperiments();
      setHistory(rows.filter((row) => row.lead_id === lead.id));
    } catch {
      setHistory([]);
    }
  }, [lead.id]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const runCompare = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await api.runExperimentCompare({
        lead_id: lead.id,
        agent_name: "qualification",
        version_a: "v1",
        version_b: "v2",
      });
      setLatest(result);
      await loadHistory();
    } catch {
      setError("Experiment failed. Ensure the lead exists and the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const display = latest ?? history[0] ?? null;

  return (
    <div className="experiments-section">
      <div className="section-header">
        <h2>Prompt A/B — Qualification</h2>
        <div className="experiment-controls">
          <button
            type="button"
            className="btn-primary"
            disabled={loading}
            onClick={runCompare}
          >
            {loading ? "Running…" : "Run v1 vs v2"}
          </button>
        </div>
      </div>
      <p className="meta">
        Compare qualification prompt versions on <strong>{lead.company_name}</strong> without
        re-running the full pipeline.
      </p>
      {error && <p className="error">{error}</p>}
      {display ? <ExperimentResult display={display} /> : null}
      {!display && !loading && (
        <p className="empty">No experiments yet for this lead. Run v1 vs v2 to compare prompts.</p>
      )}
    </div>
  );
}
