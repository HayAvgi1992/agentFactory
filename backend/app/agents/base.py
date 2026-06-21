"""Shared helpers for GTM agents — vision §6 design philosophy."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from openai import OpenAI

from app.config import settings

AGENT_PHILOSOPHY = """
Agent design philosophy:
- Retrieve and use provided context; never invent CRM or product facts.
- Analyze information and identify patterns before deciding.
- Reason about tradeoffs explicitly (what you considered and rejected).
- Explain decisions clearly — a human reviewer should understand WHY.
- Business thresholds are guardrails applied after your reasoning; focus on judgment.
""".strip()


def reasoning_system_prompt(role: str) -> str:
    return f"{AGENT_PHILOSOPHY}\n\nYour role: {role}\nReturn structured JSON only."


def get_client() -> Optional[OpenAI]:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def format_retrieved_context(retrieved_context: list[dict[str, Any]]) -> str:
    if not retrieved_context:
        return "No retrieved context."
    lines = []
    for item in retrieved_context[:5]:
        lines.append(
            f"- [{item.get('source')}] {item.get('title', item.get('document_id'))}: "
            f"{item.get('snippet', '')[:200]}"
        )
    return "\n".join(lines)


def call_json_agent(
    system: str,
    prompt: str,
    *,
    temperature: float = 0.3,
) -> Dict[str, Any]:
    client = get_client()
    if not client:
        raise RuntimeError("OpenAI client unavailable")

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=temperature,
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty response from language model")
    return json.loads(content)
