"""Prompt versioning — vision §15."""

from __future__ import annotations

from typing import Dict

DEFAULT_PROMPTS: Dict[str, Dict[str, str]] = {
    "planner": {
        "v1": (
            "Plan what business knowledge sources are needed to qualify and recommend products. "
            "Return required_sources from available sources only."
        ),
        "v2": (
            "Analyze the lead deeply before planning retrieval. Prefer CRM for named accounts, "
            "case studies for industry proof, and pricing when cost intent appears."
        ),
    },
    "qualification": {
        "v1": "Qualify on 0-100 using playbook criteria. Explain WHY with signals and risks.",
        "v2": "Score conservatively when budget is unknown. Weight CRM context heavily.",
    },
    "research": {
        "v1": "Retrieve documents via tools to populate shared state for downstream agents.",
    },
    "evaluation": {
        "v1": "Measure pipeline decision quality. Flag human review when confidence is low.",
    },
}

AGENT_PROMPT_VERSIONS: Dict[str, str] = {
    agent: "v1" for agent in DEFAULT_PROMPTS
}


def get_prompt_version(agent_name: str) -> str:
    return AGENT_PROMPT_VERSIONS.get(agent_name, "v1")


def get_prompt_instruction(agent_name: str, version: str | None = None) -> str:
    versions = DEFAULT_PROMPTS.get(agent_name, {})
    ver = version or get_prompt_version(agent_name)
    return versions.get(ver) or versions.get("v1", "")


def list_prompt_versions(agent_name: str) -> list[str]:
    return list(DEFAULT_PROMPTS.get(agent_name, {}).keys())
