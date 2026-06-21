"""Unified Pydantic normalization for agent outputs and AgentResults assembly."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.db.models import AgentRun
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
from app.state import GTMState

AGENT_ORDER = (
    "planner",
    "research",
    "qualification",
    "product_fit",
    "outreach",
    "recommendation",
    "evaluation",
)
LEGACY_AGENT_ORDER = ("qualification", "outreach", "recommendation")


def normalize_planner(data: Optional[Dict[str, Any]]) -> Optional[PlannerOutput]:
    if not data:
        return None
    return PlannerOutput(
        required_sources=list(data.get("required_sources") or []),
        reasoning=str(data.get("reasoning") or ""),
        patterns=list(data.get("patterns") or []),
        context_inputs=list(data.get("context_inputs") or []),
        prompt_version=data.get("prompt_version"),
    )


def normalize_research(
    data: Optional[Dict[str, Any]],
    retrieved_context: Optional[List[Dict[str, Any]]] = None,
) -> Optional[ResearchOutput]:
    if not data:
        return None
    return ResearchOutput(
        retrieved_documents=list(data.get("retrieved_documents") or []),
        reasoning=str(data.get("reasoning") or ""),
        patterns_identified=list(data.get("patterns_identified") or []),
        tools_used=list(data.get("tools_used") or []),
        retrieval_methods=list(data.get("retrieval_methods") or []),
        prompt_version=data.get("prompt_version"),
    )


def normalize_qualification(data: Optional[Dict[str, Any]]) -> Optional[QualificationOutput]:
    if not data:
        return None
    reasoning = str(data.get("reasoning") or data.get("reason") or "")
    try:
        return QualificationOutput(
            qualified=bool(data.get("qualified", False)),
            score=int(data.get("score", 0)),
            reason=str(data.get("reason") or reasoning),
            signals=list(data.get("signals") or []),
            risks=list(data.get("risks") or []),
            patterns=list(data.get("patterns") or []),
            tradeoffs=list(data.get("tradeoffs") or []),
            reasoning=reasoning or None,
            context_inputs=list(data.get("context_inputs") or []),
        )
    except (TypeError, ValueError):
        return None


def normalize_product_fit(data: Optional[Dict[str, Any]]) -> Optional[ProductFitOutput]:
    if not data:
        return None
    try:
        return ProductFitOutput(
            recommended_product=str(data.get("recommended_product") or ""),
            alternative_products=list(data.get("alternative_products") or []),
            confidence=float(data.get("confidence", 0)),
            matching_requirements=list(data.get("matching_requirements") or []),
            reasoning=str(data.get("reasoning") or ""),
            patterns=list(data.get("patterns") or []),
            tradeoffs=list(data.get("tradeoffs") or []),
            context_inputs=list(data.get("context_inputs") or []),
        )
    except (TypeError, ValueError):
        return None


def normalize_outreach(data: Optional[Dict[str, Any]]) -> Optional[OutreachOutput]:
    if not data:
        return None
    try:
        return OutreachOutput(
            email=str(data.get("email") or ""),
            linkedin=str(data.get("linkedin") or ""),
            questions=list(data.get("questions") or []),
            reasoning=str(data.get("reasoning") or ""),
            patterns=list(data.get("patterns") or []),
        )
    except (TypeError, ValueError):
        return None


def normalize_recommendation(data: Optional[Dict[str, Any]]) -> Optional[RecommendationOutput]:
    if not data:
        return None
    action = data.get("next_action") or data.get("action")
    if not action:
        return None
    return RecommendationOutput(
        next_action=str(action),
        reasoning=str(data.get("reasoning") or ""),
        patterns=list(data.get("patterns") or []),
        tradeoffs=list(data.get("tradeoffs") or []),
    )


def normalize_evaluation(data: Optional[Dict[str, Any]]) -> Optional[EvaluationAgentOutput]:
    if not data:
        return None
    try:
        return EvaluationAgentOutput(
            confidence=float(data.get("confidence", 0)),
            needs_human_review=bool(data.get("needs_human_review", False)),
            missing_information=list(data.get("missing_information") or []),
            reasoning=str(data.get("reasoning") or ""),
            context_inputs=list(data.get("context_inputs") or []),
            prompt_version=data.get("prompt_version"),
        )
    except (TypeError, ValueError):
        return None


def normalize_retrieved_context(items: Optional[List[Dict[str, Any]]]) -> List[RetrievedContextItem]:
    if not items:
        return []
    result: List[RetrievedContextItem] = []
    for item in items:
        try:
            result.append(
                RetrievedContextItem(
                    source=str(item.get("source") or ""),
                    document_id=str(item.get("document_id") or ""),
                    title=str(item.get("title") or ""),
                    snippet=str(item.get("snippet") or ""),
                )
            )
        except (TypeError, ValueError):
            continue
    return result


def build_agent_results_from_state(
    state: GTMState,
    processing_time_ms: int,
) -> Optional[AgentResults]:
    """Build AgentResults from graph state (full or partial after pipeline_error)."""
    require_full = not state.get("pipeline_error")
    return _assemble_results(
        planner=state.get("planner"),
        research=state.get("research"),
        qualification=state.get("qualification"),
        product_fit=state.get("product_fit"),
        outreach=state.get("outreach"),
        recommendation=state.get("recommendation"),
        evaluation=state.get("evaluation"),
        retrieved_context=state.get("retrieved_context"),
        processing_time_ms=processing_time_ms,
        require_full=require_full,
    )


def _outputs_from_runs(by_name: Dict[str, AgentRun]) -> tuple[
    Optional[Dict[str, Any]],
    Optional[Dict[str, Any]],
    Optional[Dict[str, Any]],
    Optional[Dict[str, Any]],
    Optional[Dict[str, Any]],
    Optional[Dict[str, Any]],
    Optional[Dict[str, Any]],
    Optional[List[Dict[str, Any]]],
]:
    research_run = by_name.get("research")
    retrieved_context = None
    if research_run is not None:
        retrieved_context = research_run.output.get("retrieved_context")

    return (
        by_name["planner"].output if "planner" in by_name else None,
        by_name["research"].output if "research" in by_name else None,
        by_name["qualification"].output if "qualification" in by_name else None,
        by_name["product_fit"].output if "product_fit" in by_name else None,
        by_name["outreach"].output if "outreach" in by_name else None,
        by_name["recommendation"].output if "recommendation" in by_name else None,
        by_name["evaluation"].output if "evaluation" in by_name else None,
        retrieved_context,
    )


def build_agent_results_from_runs(
    runs: List[AgentRun],
    processing_time_ms: Optional[int] = None,
) -> Optional[AgentResults]:
    by_name = {run.agent_name: run for run in runs}

    if all(name in by_name for name in AGENT_ORDER):
        (
            planner,
            research,
            qualification,
            product_fit,
            outreach,
            recommendation,
            evaluation,
            retrieved_context,
        ) = _outputs_from_runs(by_name)
        elapsed = processing_time_ms
        if elapsed is None:
            first_at = by_name["planner"].created_at
            last_at = by_name["evaluation"].created_at
            elapsed = (
                int((last_at - first_at).total_seconds() * 1000)
                if first_at and last_at
                else 0
            )
        return _assemble_results(
            planner=planner,
            research=research,
            qualification=qualification,
            product_fit=product_fit,
            outreach=outreach,
            recommendation=recommendation,
            evaluation=evaluation,
            retrieved_context=retrieved_context,
            processing_time_ms=elapsed,
            require_full=True,
        )

    if all(name in by_name for name in LEGACY_AGENT_ORDER):
        first_at = by_name["qualification"].created_at
        last_at = by_name["recommendation"].created_at
        elapsed = processing_time_ms
        if elapsed is None:
            elapsed = (
                int((last_at - first_at).total_seconds() * 1000)
                if first_at and last_at
                else 0
            )
        qualification = normalize_qualification(by_name["qualification"].output)
        outreach = normalize_outreach(by_name["outreach"].output)
        recommendation = normalize_recommendation(by_name["recommendation"].output)
        if not qualification or not outreach or not recommendation:
            return None
        return AgentResults(
            qualification=qualification,
            outreach=outreach,
            recommendation=recommendation,
            processing_time_ms=elapsed,
        )

    if "qualification" not in by_name:
        return None

    (
        planner,
        research,
        qualification,
        product_fit,
        outreach,
        recommendation,
        evaluation,
        retrieved_context,
    ) = _outputs_from_runs(by_name)
    elapsed = processing_time_ms if processing_time_ms is not None else 0
    return _assemble_results(
        planner=planner,
        research=research,
        qualification=qualification,
        product_fit=product_fit,
        outreach=outreach,
        recommendation=recommendation,
        evaluation=evaluation,
        retrieved_context=retrieved_context,
        processing_time_ms=elapsed,
        require_full=False,
    )


def _assemble_results(
    *,
    planner: Optional[Dict[str, Any]],
    research: Optional[Dict[str, Any]],
    qualification: Optional[Dict[str, Any]],
    product_fit: Optional[Dict[str, Any]],
    outreach: Optional[Dict[str, Any]],
    recommendation: Optional[Dict[str, Any]],
    evaluation: Optional[Dict[str, Any]],
    retrieved_context: Optional[List[Dict[str, Any]]],
    processing_time_ms: int,
    require_full: bool,
) -> Optional[AgentResults]:
    norm_planner = normalize_planner(planner)
    norm_research = normalize_research(research, retrieved_context)
    norm_qualification = normalize_qualification(qualification)
    norm_product_fit = normalize_product_fit(product_fit)
    norm_outreach = normalize_outreach(outreach)
    norm_recommendation = normalize_recommendation(recommendation)
    norm_evaluation = normalize_evaluation(evaluation)
    norm_context = normalize_retrieved_context(retrieved_context)

    if require_full:
        required = (
            norm_planner,
            norm_research,
            norm_qualification,
            norm_product_fit,
            norm_outreach,
            norm_recommendation,
            norm_evaluation,
        )
        if any(item is None for item in required):
            return None

    if not norm_qualification:
        return None

    return AgentResults(
        planner=norm_planner,
        research=norm_research,
        qualification=norm_qualification,
        product_fit=norm_product_fit,
        outreach=norm_outreach,
        recommendation=norm_recommendation,
        evaluation=norm_evaluation,
        retrieved_context=norm_context,
        processing_time_ms=processing_time_ms,
    )
