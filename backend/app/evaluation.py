"""Aggregate GTM KPIs from persisted agent runs."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.db.models import Lead
from app.repository import AGENT_ORDER
from app.schemas import EvaluationMetrics


def compute_evaluation_metrics(
    db: Session,
    lead_ids: Optional[List[int]] = None,
) -> EvaluationMetrics:
    """Compute business KPIs from leads and their agent_runs.

    Rates use total_leads as the denominator (including partial/failed pipelines).
    Average score includes only leads with a qualification run.
    """
    query = db.query(Lead).options(joinedload(Lead.agent_runs))
    if lead_ids is not None:
        query = query.filter(Lead.id.in_(lead_ids))

    leads = query.all()
    total_leads = len(leads)

    qualified_leads = 0
    meeting_recommendations = 0
    processed_leads = 0
    score_sum = 0
    score_count = 0

    for lead in leads:
        by_name = {run.agent_name: run for run in lead.agent_runs}

        qualification = by_name.get("qualification")
        if qualification is not None:
            output = qualification.output
            if bool(output.get("qualified")):
                qualified_leads += 1
            score_sum += int(output.get("score", 0))
            score_count += 1

        recommendation = by_name.get("recommendation")
        if recommendation is not None and recommendation.output.get("next_action") == "book_meeting":
            meeting_recommendations += 1

        if all(name in by_name for name in AGENT_ORDER):
            processed_leads += 1

    qualification_rate = qualified_leads / total_leads if total_leads else 0.0
    meeting_recommendation_rate = (
        meeting_recommendations / total_leads if total_leads else 0.0
    )
    average_score = score_sum / score_count if score_count else None

    return EvaluationMetrics(
        total_leads=total_leads,
        qualified_leads=qualified_leads,
        qualification_rate=qualification_rate,
        meeting_recommendations=meeting_recommendations,
        meeting_recommendation_rate=meeting_recommendation_rate,
        average_score=average_score,
        processed_leads=processed_leads,
    )
