import { Card, StatCard } from "@/components/Card";
import type { EvaluationMetrics } from "@/lib/api";
import { MONDAY } from "@/lib/utils";

interface EvaluationMetricsProps {
  metrics: EvaluationMetrics | null;
}

function formatRate(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}

export function EvaluationMetricsPanel({ metrics }: EvaluationMetricsProps) {
  if (!metrics) {
    return (
      <Card title="GTM Metrics">
        <p className="empty">Metrics unavailable — is the backend running?</p>
      </Card>
    );
  }

  const avgScore =
    metrics.average_score !== null ? Math.round(metrics.average_score) : null;

  return (
    <Card title="GTM Metrics">
      <div className="stat-grid">
        <StatCard label="Total Leads" value={metrics.total_leads} />
        <StatCard
          label="Qualified Leads"
          value={metrics.qualified_leads}
          subtitle={`${formatRate(metrics.qualification_rate)} qualification rate`}
          accent={MONDAY.green}
        />
        <StatCard
          label="Average Score"
          value={avgScore !== null ? avgScore : "—"}
          subtitle="out of 100"
        />
        <StatCard
          label="Meeting Rate"
          value={formatRate(metrics.meeting_recommendation_rate)}
          subtitle={`${metrics.meeting_recommendations} book meeting`}
          accent="hsla(240, 100%, 69.02%, 1)"
        />
      </div>
    </Card>
  );
}
