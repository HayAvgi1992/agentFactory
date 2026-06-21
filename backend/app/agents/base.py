"""Shared helpers for GTM agents."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from openai import OpenAI

from app.config import settings


def get_client() -> Optional[OpenAI]:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


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
    return json.loads(response.choices[0].message.content)
