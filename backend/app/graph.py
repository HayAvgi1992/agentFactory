"""LangGraph workflow — 7-agent target architecture with shared GTMState."""

from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

from langgraph.graph import END, StateGraph

from app.agents.evaluation_agent import run_evaluation_agent
from app.agents.outreach_agent import run_outreach_agent
from app.agents.planner_agent import run_planner_agent
from app.agents.product_fit_agent import run_product_fit_agent
from app.agents.qualification_agent import run_qualification_agent
from app.agents.recommendation_agent import run_recommendation_agent
from app.agents.research_agent import run_research_agent
from app.state import GTMState

NodeFn = Callable[[GTMState], Dict[str, Any]]


def planner_node(state: GTMState) -> Dict[str, Any]:
    return {"planner": run_planner_agent(state)}


def research_node(state: GTMState) -> Dict[str, Any]:
    result = run_research_agent(state)
    return {
        "retrieved_context": result["retrieved_context"],
        "research": {"retrieved_documents": result["retrieved_documents"]},
    }


def qualification_node(state: GTMState) -> Dict[str, Any]:
    return {"qualification": run_qualification_agent(state)}


def product_fit_node(state: GTMState) -> Dict[str, Any]:
    return {"product_fit": run_product_fit_agent(state)}


def outreach_node(state: GTMState) -> Dict[str, Any]:
    return {"outreach": run_outreach_agent(state)}


def recommendation_node(state: GTMState) -> Dict[str, Any]:
    return {"recommendation": run_recommendation_agent(state)}


def evaluation_node(state: GTMState) -> Dict[str, Any]:
    return {"evaluation": run_evaluation_agent(state)}


# Ordered steps for sequential execution with per-step error handling.
AGENT_STEPS: Tuple[Tuple[str, str, NodeFn], ...] = (
    ("planner", "planner", planner_node),
    ("research", "research", research_node),
    ("qualification", "qualification", qualification_node),
    ("product_fit", "product_fit", product_fit_node),
    ("outreach", "outreach", outreach_node),
    ("recommendation", "recommendation", recommendation_node),
    ("evaluation", "evaluation", evaluation_node),
)


def build_graph():
    """Compile the LangGraph state machine for the full GTM workflow."""
    workflow = StateGraph(GTMState)
    node_names = {
        "planner": "planner_step",
        "research": "research_step",
        "qualification": "qualification_step",
        "product_fit": "product_fit_step",
        "outreach": "outreach_step",
        "recommendation": "recommendation_step",
        "evaluation": "evaluation_step",
    }
    for step_id, node_name, node_fn in (
        (step_id, node_names[step_id], node_fn) for step_id, _, node_fn in AGENT_STEPS
    ):
        workflow.add_node(node_name, node_fn)

    workflow.set_entry_point("planner_step")
    workflow.add_edge("planner_step", "research_step")
    workflow.add_edge("research_step", "qualification_step")
    workflow.add_edge("qualification_step", "product_fit_step")
    workflow.add_edge("product_fit_step", "outreach_step")
    workflow.add_edge("outreach_step", "recommendation_step")
    workflow.add_edge("recommendation_step", "evaluation_step")
    workflow.add_edge("evaluation_step", END)
    return workflow.compile()
