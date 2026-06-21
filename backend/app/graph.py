"""LangGraph workflow — sole orchestrator for the 7-agent GTM pipeline."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Tuple

from langgraph.graph import END, StateGraph

from app.agents.evaluation_agent import run_evaluation_agent
from app.agents.outreach_agent import run_outreach_agent
from app.agents.planner_agent import run_planner_agent
from app.agents.product_fit_agent import run_product_fit_agent
from app.agents.qualification_agent import run_qualification_agent
from app.agents.recommendation_agent import run_recommendation_agent
from app.agents.research_agent import run_research_agent
from app.config import settings
from app.state import (
    AgentRunDict,
    GTMState,
    agent_output_from_state,
    snapshot_for_agent,
)

NodeFn = Callable[[GTMState], Dict[str, Any]]

_COMPILED_GRAPH = None


def _planner_impl(state: GTMState) -> Dict[str, Any]:
    return {"planner": run_planner_agent(state)}


def _research_impl(state: GTMState) -> Dict[str, Any]:
    result = run_research_agent(state)
    return {
        "retrieved_context": result["retrieved_context"],
        "research": {
            "retrieved_documents": result["retrieved_documents"],
            "patterns_identified": result.get("patterns_identified", []),
            "reasoning": result.get("reasoning", ""),
        },
    }


def _qualification_impl(state: GTMState) -> Dict[str, Any]:
    return {"qualification": run_qualification_agent(state)}


def _product_fit_impl(state: GTMState) -> Dict[str, Any]:
    return {"product_fit": run_product_fit_agent(state)}


def _outreach_impl(state: GTMState) -> Dict[str, Any]:
    return {"outreach": run_outreach_agent(state)}


def _recommendation_impl(state: GTMState) -> Dict[str, Any]:
    return {"recommendation": run_recommendation_agent(state)}


def _evaluation_impl(state: GTMState) -> Dict[str, Any]:
    return {"evaluation": run_evaluation_agent(state)}


AGENT_STEPS: Tuple[Tuple[str, str, NodeFn], ...] = (
    ("planner", "planner", _planner_impl),
    ("research", "research", _research_impl),
    ("qualification", "qualification", _qualification_impl),
    ("product_fit", "product_fit", _product_fit_impl),
    ("outreach", "outreach", _outreach_impl),
    ("recommendation", "recommendation", _recommendation_impl),
    ("evaluation", "evaluation", _evaluation_impl),
)

_NODE_NAMES = {
    "planner": "planner_step",
    "research": "research_step",
    "qualification": "qualification_step",
    "product_fit": "product_fit_step",
    "outreach": "outreach_step",
    "recommendation": "recommendation_step",
    "evaluation": "evaluation_step",
}


def _instrument_node(
    step_index: int,
    step_id: str,
    agent_name: str,
    inner: NodeFn,
) -> Callable[[GTMState], Dict[str, Any]]:
    """Wrap an agent node with delay, run recording, and error capture."""

    def node(state: GTMState) -> Dict[str, Any]:
        if state.get("pipeline_error"):
            return {}

        time.sleep(settings.step_delay_sec)
        agent_input = snapshot_for_agent(state, agent_name)

        try:
            patch = inner(state)
            merged: GTMState = {**state, **patch}  # type: ignore[typeddict-item]
            run: AgentRunDict = {
                "agent_name": agent_name,
                "input": agent_input,
                "output": agent_output_from_state(merged, agent_name),
            }
            return {**patch, "agent_runs": [run]}
        except Exception as exc:
            return {
                "pipeline_error": {
                    "step_index": step_index,
                    "step_id": step_id,
                    "message": str(exc),
                },
            }

    return node


def build_graph():
    """Compile and cache the LangGraph state machine."""
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is not None:
        return _COMPILED_GRAPH

    workflow = StateGraph(GTMState)
    for index, (step_id, agent_name, inner) in enumerate(AGENT_STEPS, start=1):
        node_name = _NODE_NAMES[step_id]
        workflow.add_node(
            node_name,
            _instrument_node(index, step_id, agent_name, inner),
        )

    workflow.set_entry_point("planner_step")
    workflow.add_edge("planner_step", "research_step")
    workflow.add_edge("research_step", "qualification_step")
    workflow.add_edge("qualification_step", "product_fit_step")
    workflow.add_edge("product_fit_step", "outreach_step")
    workflow.add_edge("outreach_step", "recommendation_step")
    workflow.add_edge("recommendation_step", "evaluation_step")
    workflow.add_edge("evaluation_step", END)

    _COMPILED_GRAPH = workflow.compile()
    return _COMPILED_GRAPH
