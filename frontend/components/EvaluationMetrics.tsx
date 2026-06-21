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
  const avgConfidence =
    metrics.average_confidence !== null
      ? Math.round(metrics.average_confidence * 100)
      : null;

  return (
    <Card title="GTM Metrics">
      <div className="stats-row">
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
        <StatCard
          label="Avg Confidence"
          value={avgConfidence !== null ? `${avgConfidence}%` : "—"}
          subtitle="evaluation agent"
        />
        <StatCard
          label="Human Review"
          value={formatRate(metrics.human_review_rate)}
          subtitle={`${metrics.human_review_count} flagged`}
          accent={MONDAY.yellow}
        />
      </div>
    </Card>
  );
}
