"""Shared GTMState for the LangGraph agent workflow (vision §5)."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

# ---------------------------------------------------------------------------
# Vision §5 — business slices every agent reads / writes
# ---------------------------------------------------------------------------
SHARED_STATE_FIELDS = (
    "lead",
    "retrieved_context",
    "qualification",
    "product_fit",
    "outreach",
    "recommendation",
    "evaluation",
)

# Extended slices (planner → research flow)
EXTENDED_STATE_FIELDS = ("planner", "research")

# Orchestration-only fields (not part of business snapshot)
ORCHESTRATION_FIELDS = ("agent_runs", "pipeline_error")

# Which state keys each agent reads when it executes
AGENT_READS: Dict[str, tuple[str, ...]] = {
    "planner": ("lead",),
    "research": ("lead", "planner"),
    "qualification": ("lead", "retrieved_context"),
    "product_fit": ("lead", "qualification", "retrieved_context"),
    "outreach": ("lead", "qualification", "product_fit"),
    "recommendation": ("lead", "qualification", "product_fit", "outreach"),
    "evaluation": (
        "lead",
        "retrieved_context",
        "qualification",
        "product_fit",
        "outreach",
        "recommendation",
    ),
}

# Which state key each agent writes
AGENT_WRITES: Dict[str, str] = {
    "planner": "planner",
    "research": "retrieved_context",
    "qualification": "qualification",
    "product_fit": "product_fit",
    "outreach": "outreach",
    "recommendation": "recommendation",
    "evaluation": "evaluation",
}


class PipelineError(TypedDict):
    step_index: int
    step_id: str
    message: str


class AgentRunDict(TypedDict, total=False):
    agent_name: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    prompt_version: str
    tools_used: List[str]
    retrieved_documents: List[str]
    confidence: float
    latency_ms: int
    token_usage: int


class GTMState(TypedDict, total=False):
    """LangGraph shared state — all agents operate on this object."""

    # Vision §5 core
    lead: Dict[str, Any]
    retrieved_context: List[Dict[str, Any]]
    qualification: Dict[str, Any]
    product_fit: Dict[str, Any]
    outreach: Dict[str, Any]
    recommendation: Dict[str, Any]
    evaluation: Dict[str, Any]
    # Extended (information gathering)
    planner: Dict[str, Any]
    research: Dict[str, Any]
    # Orchestration
    agent_runs: Annotated[List[AgentRunDict], operator.add]
    pipeline_error: PipelineError


def initial_state(lead_data: Dict[str, Any]) -> GTMState:
    return {
        "lead": dict(lead_data),
        "retrieved_context": [],
        "agent_runs": [],
    }


# ---------------------------------------------------------------------------
# Read helpers — agents use these instead of raw state[key]
# ---------------------------------------------------------------------------


def get_lead(state: GTMState) -> Dict[str, Any]:
    return state.get("lead") or {}


def get_planner(state: GTMState) -> Dict[str, Any]:
    return state.get("planner") or {}


def get_research(state: GTMState) -> Dict[str, Any]:
    return state.get("research") or {}


def get_retrieved_context(state: GTMState) -> List[Dict[str, Any]]:
    return state.get("retrieved_context") or []


def get_qualification(state: GTMState) -> Dict[str, Any]:
    return state.get("qualification") or {}


def get_product_fit(state: GTMState) -> Dict[str, Any]:
    return state.get("product_fit") or {}


def get_outreach(state: GTMState) -> Dict[str, Any]:
    return state.get("outreach") or {}


def get_recommendation(state: GTMState) -> Dict[str, Any]:
    return state.get("recommendation") or {}


def get_evaluation(state: GTMState) -> Dict[str, Any]:
    return state.get("evaluation") or {}


def get_slice(state: GTMState, key: str) -> Any:
    return state.get(key)  # type: ignore[literal-required]


# ---------------------------------------------------------------------------
# Snapshot helpers — audit trail + API
# ---------------------------------------------------------------------------


def snapshot_for_agent(state: GTMState, agent_name: str) -> Dict[str, Any]:
    """Build the input snapshot stored before an agent runs."""
    reads = AGENT_READS.get(agent_name, ())
    snapshot: Dict[str, Any] = {}
    for key in reads:
        value = get_slice(state, key)
        if value is not None:
            snapshot[key] = value
    return snapshot


def agent_output_from_state(state: GTMState, agent_name: str) -> Dict[str, Any]:
    """Extract the persisted output dict for an agent run record."""
    if agent_name == "research":
        research = get_research(state)
        return {
            "retrieved_documents": research.get("retrieved_documents", []),
            "retrieved_context": get_retrieved_context(state),
            "patterns_identified": research.get("patterns_identified", []),
            "reasoning": research.get("reasoning", ""),
            "tools_used": research.get("tools_used", []),
            "retrieval_methods": research.get("retrieval_methods", []),
            "prompt_version": research.get("prompt_version"),
        }
    write_key = AGENT_WRITES.get(agent_name, agent_name)
    return dict(get_slice(state, write_key) or {})


def public_state_snapshot(state: GTMState) -> Dict[str, Any]:
    """Business shared-state view (vision §5 + planner/research extensions)."""
    all_fields = (*SHARED_STATE_FIELDS, *EXTENDED_STATE_FIELDS)
    snapshot: Dict[str, Any] = {}
    populated: List[str] = []

    for key in all_fields:
        value = get_slice(state, key)
        if value is None:
            continue
        if isinstance(value, (list, dict)) and not value:
            continue
        snapshot[key] = value
        populated.append(key)

    snapshot["populated_fields"] = populated
    return snapshot


def populated_field_count(state: GTMState) -> int:
    return len(public_state_snapshot(state).get("populated_fields", []))


def build_state_snapshot(state: GTMState):
    """Build API-ready GTMStateSnapshot from graph state."""
    from app.schemas import GTMStateSnapshot, RetrievedContextItem

    raw = public_state_snapshot(state)
    context_items = [
        RetrievedContextItem(
            source=str(item.get("source") or ""),
            document_id=str(item.get("document_id") or ""),
            title=str(item.get("title") or ""),
            snippet=str(item.get("snippet") or ""),
        )
        for item in raw.get("retrieved_context") or []
    ]

    return GTMStateSnapshot(
        lead=raw.get("lead") or state.get("lead") or {},
        planner=raw.get("planner"),
        research=raw.get("research"),
        retrieved_context=context_items,
        qualification=raw.get("qualification"),
        product_fit=raw.get("product_fit"),
        outreach=raw.get("outreach"),
        recommendation=raw.get("recommendation"),
        evaluation=raw.get("evaluation"),
        populated_fields=list(raw.get("populated_fields") or []),
    )

