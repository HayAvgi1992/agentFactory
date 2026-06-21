"""LangGraph-only GTM pipeline entry point."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Literal, Optional

from app.graph import build_graph
from app.results_builder import build_agent_results_from_state
from app.schemas import AgentResults, AgentRunRecord
from app.state import GTMState, initial_state

PipelineStatus = Literal["complete", "partial"]


@dataclass
class PipelineResult:
    status: PipelineStatus
    runs: List[AgentRunRecord] = field(default_factory=list)
    results: Optional[AgentResults] = None
    error: Optional[str] = None
    failed_step: Optional[int] = None
    step_id: Optional[str] = None
    processing_time_ms: int = 0


def _validate_lead(lead_data: dict) -> None:
    if not lead_data.get("company_name"):
        raise ValueError("Company name is required")
    if not lead_data.get("message"):
        raise ValueError("Lead message is required")


def _runs_from_state(state: GTMState) -> List[AgentRunRecord]:
    return [
        AgentRunRecord(
            agent_name=run["agent_name"],
            input=run["input"],
            output=run["output"],
        )
        for run in state.get("agent_runs") or []
    ]


def run_pipeline(lead_data: dict) -> PipelineResult:
    """Execute the GTM workflow via LangGraph build_graph().invoke()."""
    start = time.time()

    try:
        _validate_lead(lead_data)
    except ValueError as exc:
        return PipelineResult(
            status="partial",
            error=str(exc),
            failed_step=0,
            step_id="input",
        )

    graph = build_graph()
    final_state: GTMState = graph.invoke(initial_state(lead_data))
    elapsed_ms = int((time.time() - start) * 1000)
    runs = _runs_from_state(final_state)

    pipeline_error = final_state.get("pipeline_error")
    if pipeline_error:
        return PipelineResult(
            status="partial",
            runs=runs,
            results=build_agent_results_from_state(final_state, elapsed_ms),
            error=pipeline_error["message"],
            failed_step=pipeline_error["step_index"],
            step_id=pipeline_error["step_id"],
            processing_time_ms=elapsed_ms,
        )

    return PipelineResult(
        status="complete",
        runs=runs,
        results=build_agent_results_from_state(final_state, elapsed_ms),
        processing_time_ms=elapsed_ms,
    )
