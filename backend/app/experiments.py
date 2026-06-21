"""Prompt A/B comparison — vision §15–16."""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.agents.qualification_agent import run_qualification_agent
from app.db.models import ExperimentRun, Lead
from app.prompts.registry import AGENT_PROMPT_VERSIONS, get_prompt_instruction
from app.state import initial_state


def _run_qualification_variant(lead: Lead, version: str) -> Dict[str, Any]:
    prior = AGENT_PROMPT_VERSIONS.get("qualification")
    AGENT_PROMPT_VERSIONS["qualification"] = version
    try:
        state = initial_state(
            {
                "company_name": lead.company_name,
                "industry": lead.industry,
                "company_size": lead.company_size,
                "message": lead.message,
            }
        )
        return run_qualification_agent(state)
    finally:
        if prior is not None:
            AGENT_PROMPT_VERSIONS["qualification"] = prior


def _pick_winner(result_a: Dict[str, Any], result_b: Dict[str, Any]) -> str:
    score_a = int(result_a.get("score", 0))
    score_b = int(result_b.get("score", 0))
    if score_a > score_b:
        return "version_a"
    if score_b > score_a:
        return "version_b"
    return "tie"


def list_experiments(db: Session, limit: int = 20) -> List[ExperimentRun]:
    return (
        db.query(ExperimentRun)
        .order_by(ExperimentRun.id.desc())
        .limit(limit)
        .all()
    )


def compare_prompt_versions(
    db: Session,
    *,
    lead_id: int,
    agent_name: str,
    version_a: str,
    version_b: str,
) -> ExperimentRun | None:
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return None

    if agent_name != "qualification":
        raise ValueError(f"Experiment not implemented for agent: {agent_name}")

    result_a = _run_qualification_variant(lead, version_a)
    result_b = _run_qualification_variant(lead, version_b)
    winner = _pick_winner(result_a, result_b)
    metrics = {
        "qualification_rate_a": 1.0 if result_a.get("qualified") else 0.0,
        "qualification_rate_b": 1.0 if result_b.get("qualified") else 0.0,
        "average_score_a": int(result_a.get("score", 0)),
        "average_score_b": int(result_b.get("score", 0)),
        "prompt_a": get_prompt_instruction(agent_name, version_a),
        "prompt_b": get_prompt_instruction(agent_name, version_b),
    }

    record = ExperimentRun(
        lead_id=lead_id,
        agent_name=agent_name,
        version_a=version_a,
        version_b=version_b,
        result_a=result_a,
        result_b=result_b,
        winner=winner,
        metrics=metrics,
    )
    db.add(record)
    db.flush()
    return record
