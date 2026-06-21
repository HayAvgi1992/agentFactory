"""Simple sequential pipeline for Phase 1 MVP — no LangGraph, no Vector DB."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, TypeVar

from app.agents.outreach_agent import run_outreach_agent
from app.agents.qualification_agent import run_qualification_agent
from app.agents.recommendation_agent import run_recommendation_agent
from app.config import settings
from app.schemas import AgentResults, OutreachOutput, QualificationOutput, RecommendationOutput

T = TypeVar("T")

STEP_IDS = ("input", "qualification", "outreach", "recommendation")


class PipelineStepError(Exception):
    def __init__(
        self,
        step_index: int,
        step_id: str,
        message: str,
        runs: List[AgentRunRecord] | None = None,
    ):
        self.step_index = step_index
        self.step_id = step_id
        self.message = message
        self.runs = runs or []
        super().__init__(message)


@dataclass
class AgentRunRecord:
    agent_name: str
    input: Dict[str, Any]
    output: Dict[str, Any]


@dataclass
class PipelineResult:
    results: AgentResults
    runs: List[AgentRunRecord] = field(default_factory=list)


def _validate_lead(lead_data: Dict[str, Any]) -> None:
    if not lead_data.get("company_name"):
        raise ValueError("Company name is required")
    if not lead_data.get("message"):
        raise ValueError("Lead message is required")


def _run_step(step_index: int, step_id: str, fn: Callable[[], T]) -> T:
    time.sleep(settings.step_delay_sec)
    try:
        return fn()
    except Exception as e:
        raise PipelineStepError(step_index, step_id, str(e)) from e


def run_pipeline(lead_data: Dict[str, Any]) -> PipelineResult:
    start = time.time()
    runs: List[AgentRunRecord] = []

    try:
        _run_step(0, "input", lambda: _validate_lead(lead_data))

        qualification_input = dict(lead_data)
        qualification = _run_step(
            1,
            "qualification",
            lambda: run_qualification_agent(lead_data),
        )
        runs.append(
            AgentRunRecord(
                agent_name="qualification",
                input=qualification_input,
                output=dict(qualification),
            )
        )

        outreach_input = {"lead_data": lead_data, "qualification": qualification}
        outreach = _run_step(
            2,
            "outreach",
            lambda: run_outreach_agent(lead_data, qualification),
        )
        runs.append(
            AgentRunRecord(
                agent_name="outreach",
                input=outreach_input,
                output=dict(outreach),
            )
        )

        recommendation_input = {
            "lead_data": lead_data,
            "qualification": qualification,
            "outreach": outreach,
        }
        recommendation = _run_step(
            3,
            "recommendation",
            lambda: run_recommendation_agent(lead_data, qualification, outreach),
        )
        runs.append(
            AgentRunRecord(
                agent_name="recommendation",
                input=recommendation_input,
                output=dict(recommendation),
            )
        )
    except PipelineStepError as e:
        raise PipelineStepError(e.step_index, e.step_id, e.message, runs=runs) from e

    elapsed_ms = int((time.time() - start) * 1000)

    results = AgentResults(
        qualification=QualificationOutput(
            qualified=qualification["qualified"],
            score=qualification["score"],
            reason=qualification["reason"],
        ),
        outreach=OutreachOutput(
            email=outreach["email"],
            linkedin=outreach["linkedin"],
            questions=outreach["questions"],
        ),
        recommendation=RecommendationOutput(
            next_action=recommendation["next_action"],
        ),
        processing_time_ms=elapsed_ms,
    )

    return PipelineResult(results=results, runs=runs)
