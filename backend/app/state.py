"""Shared GTMState for the agent workflow (LangGraph target architecture)."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, TypedDict


class PipelineError(TypedDict):
    step_index: int
    step_id: str
    message: str


class AgentRunDict(TypedDict):
    agent_name: str
    input: Dict[str, Any]
    output: Dict[str, Any]


class GTMState(TypedDict, total=False):
    lead: Dict[str, Any]
    planner: Dict[str, Any]
    research: Dict[str, Any]
    retrieved_context: List[Dict[str, Any]]
    qualification: Dict[str, Any]
    product_fit: Dict[str, Any]
    outreach: Dict[str, Any]
    recommendation: Dict[str, Any]
    evaluation: Dict[str, Any]
    agent_runs: Annotated[List[AgentRunDict], operator.add]
    pipeline_error: PipelineError


def initial_state(lead_data: Dict[str, Any]) -> GTMState:
    return {
        "lead": dict(lead_data),
        "retrieved_context": [],
        "agent_runs": [],
    }
