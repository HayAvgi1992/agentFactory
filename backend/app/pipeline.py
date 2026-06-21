"""LangGraph-backed GTM pipeline with shared state (Phase 4 target architecture)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, TypeVar

from app.config import settings
from app.graph import AGENT_STEPS
from app.schemas import (
    AgentResults,
    EvaluationAgentOutput,
    OutreachOutput,
    PlannerOutput,
    ProductFitOutput,
    QualificationOutput,
    RecommendationOutput,
    ResearchOutput,
    RetrievedContextItem,
)
from app.state import GTMState, initial_state

T = TypeVar("T")

STEP_IDS = ("input",) + tuple(step_id for step_id, _, _ in AGENT_STEPS)


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


def _snapshot_for_agent(state: GTMState, agent_name: str) -> Dict[str, Any]:
    """Build the input snapshot stored for each agent run."""
    snapshot: Dict[str, Any] = {"lead": state.get("lead", {})}
    if agent_name != "planner":
        snapshot["planner"] = state.get("planner")
    if agent_name not in ("planner", "research"):
        snapshot["retrieved_context"] = state.get("retrieved_context", [])
    if agent_name in ("product_fit", "outreach", "recommendation", "evaluation"):
        snapshot["qualification"] = state.get("qualification")
    if agent_name in ("outreach", "recommendation", "evaluation"):
        snapshot["product_fit"] = state.get("product_fit")
    if agent_name in ("recommendation", "evaluation"):
        snapshot["outreach"] = state.get("outreach")
    if agent_name == "evaluation":
        snapshot["recommendation"] = state.get("recommendation")
    return snapshot


def _agent_output(state: GTMState, agent_name: str) -> Dict[str, Any]:
    if agent_name == "research":
        research = state.get("research") or {}
        return {
            "retrieved_documents": research.get("retrieved_documents", []),
            "retrieved_context": state.get("retrieved_context") or [],
        }
    return dict(state.get(agent_name) or {})


def run_pipeline(lead_data: Dict[str, Any]) -> PipelineResult:
    start = time.time()
    runs: List[AgentRunRecord] = []
    state: GTMState = initial_state(lead_data)

    try:
        _run_step(0, "input", lambda: _validate_lead(lead_data))

        for step_index, (step_id, agent_name, node_fn) in enumerate(AGENT_STEPS, start=1):
            agent_input = _snapshot_for_agent(state, agent_name)

            def _execute(current_state: GTMState = state, fn: Callable = node_fn) -> Dict[str, Any]:
                return fn(current_state)

            patch = _run_step(step_index, step_id, _execute)
            state = {**state, **patch}
            runs.append(
                AgentRunRecord(
                    agent_name=agent_name,
                    input=agent_input,
                    output=_agent_output(state, agent_name),
                )
            )
    except PipelineStepError as e:
        raise PipelineStepError(e.step_index, e.step_id, e.message, runs=runs) from e

    elapsed_ms = int((time.time() - start) * 1000)
    results = _build_results(state, elapsed_ms)
    return PipelineResult(results=results, runs=runs)


def _build_results(state: GTMState, processing_time_ms: int) -> AgentResults:
    qualification = state["qualification"]
    outreach = state["outreach"]
    recommendation = state["recommendation"]
    planner = state.get("planner") or {}
    research = state.get("research") or {}
    product_fit = state.get("product_fit") or {}
    evaluation = state.get("evaluation") or {}
    retrieved_context = state.get("retrieved_context") or []

    return AgentResults(
        planner=PlannerOutput(required_sources=list(planner.get("required_sources", []))),
        research=ResearchOutput(
            retrieved_documents=list(research.get("retrieved_documents", [])),
        ),
        qualification=QualificationOutput(
            qualified=qualification["qualified"],
            score=qualification["score"],
            reason=qualification.get("reason", qualification.get("reasoning", "")),
            signals=list(qualification.get("signals", [])),
            risks=list(qualification.get("risks", [])),
            reasoning=qualification.get("reasoning", qualification.get("reason", "")),
        ),
        product_fit=ProductFitOutput(
            recommended_product=product_fit.get("recommended_product", ""),
            alternative_products=list(product_fit.get("alternative_products", [])),
            confidence=float(product_fit.get("confidence", 0)),
            matching_requirements=list(product_fit.get("matching_requirements", [])),
            reasoning=product_fit.get("reasoning", ""),
        ),
        outreach=OutreachOutput(
            email=outreach["email"],
            linkedin=outreach["linkedin"],
            questions=outreach["questions"],
        ),
        recommendation=RecommendationOutput(
            next_action=recommendation["next_action"],
        ),
        evaluation=EvaluationAgentOutput(
            confidence=float(evaluation.get("confidence", 0)),
            needs_human_review=bool(evaluation.get("needs_human_review", False)),
            missing_information=list(evaluation.get("missing_information", [])),
        ),
        retrieved_context=[
            RetrievedContextItem(
                source=item.get("source", ""),
                document_id=item.get("document_id", ""),
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
            )
            for item in retrieved_context
        ],
        processing_time_ms=processing_time_ms,
    )
