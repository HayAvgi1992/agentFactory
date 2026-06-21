"""Observability helpers — vision §18."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def extract_observability(agent_name: str, output: Dict[str, Any]) -> Dict[str, Any]:
    obs: Dict[str, Any] = {
        "prompt_version": output.get("prompt_version"),
        "tools_used": output.get("tools_used"),
        "retrieved_documents": output.get("retrieved_documents"),
        "confidence": output.get("confidence"),
        "token_usage": output.get("token_usage"),
    }
    if agent_name == "research" and not obs["retrieved_documents"]:
        obs["retrieved_documents"] = output.get("retrieved_documents")
    return {k: v for k, v in obs.items() if v is not None}


def build_agent_run_record(
    *,
    agent_name: str,
    agent_input: Dict[str, Any],
    output: Dict[str, Any],
    latency_ms: int,
) -> Dict[str, Any]:
    obs = extract_observability(agent_name, output)
    return {
        "agent_name": agent_name,
        "input": agent_input,
        "output": output,
        "latency_ms": latency_ms,
        **obs,
    }
