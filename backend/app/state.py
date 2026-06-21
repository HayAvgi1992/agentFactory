"""Shared GTMState for the agent workflow (LangGraph target architecture)."""

from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class GTMState(TypedDict, total=False):
    lead: Dict[str, Any]
    planner: Dict[str, Any]
    retrieved_context: List[Dict[str, Any]]
    qualification: Dict[str, Any]
    product_fit: Dict[str, Any]
    outreach: Dict[str, Any]
    recommendation: Dict[str, Any]
    evaluation: Dict[str, Any]


def initial_state(lead_data: Dict[str, Any]) -> GTMState:
    return {
        "lead": dict(lead_data),
        "retrieved_context": [],
    }
