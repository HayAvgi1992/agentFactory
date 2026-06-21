"""Qualification Agent — vision §7: decide if a lead enters the sales process."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import call_json_agent, get_client, reasoning_system_prompt
from app.agents.guardrails import (
    QUALIFICATION_THRESHOLD,
    apply_qualification_guardrails,
    check_qualification_disqualifiers,
)
from app.agents.qualification_context import (
    CASE_STUDY_SOURCE,
    CRM_SOURCE,
    ICP_INDUSTRIES,
    PLAYBOOK_SCORING,
    PLAYBOOK_SOURCE,
    PRODUCT_SOURCE,
    available_input_labels,
    format_qualification_prompt_context,
    parse_employee_count,
    partition_qualification_context,
)
from app.state import GTMState, get_lead, get_retrieved_context

def _snippet_text(items: List[Dict[str, Any]]) -> str:
    return " ".join(str(item.get("snippet") or "") for item in items).lower()


def _score_lead(
    lead_data: Dict[str, Any],
    partitions: Dict[str, List[Dict[str, Any]]],
) -> tuple[int, List[str], List[str], List[str], List[str]]:
    message = (lead_data.get("message") or "").lower()
    industry = (lead_data.get("industry") or "").lower()
    employees = parse_employee_count(lead_data.get("company_size"))

    score = 40
    signals: List[str] = []
    risks: List[str] = []
    patterns: List[str] = []
    tradeoffs: List[str] = []

    disqualified, disqual_risks = check_qualification_disqualifiers(lead_data)
    if disqualified:
        return 15, signals, disqual_risks, ["Disqualifier triggered"], tradeoffs

    if any(token in message for token in ("demo", "pricing", "solution", "purchase")):
        score += PLAYBOOK_SCORING["demo_or_pricing"]
        signals.append("Pricing or solution engagement")
        patterns.append("High-intent language in inbound message")

    if any(token in message for token in ("urgent", "asap", "this quarter", "timeline")):
        score += PLAYBOOK_SCORING["urgency"]
        signals.append("Urgency expressed")
        patterns.append("Time-sensitive buying signal")

    if employees is not None and employees >= 100:
        score += PLAYBOOK_SCORING["company_size_100_plus"]
        signals.append("Mid-market company size (100+ employees)")
        patterns.append("Company size within ICP range")

    if industry in ICP_INDUSTRIES:
        score += PLAYBOOK_SCORING["industry_fit"]
        signals.append("Strong ICP fit")
        patterns.append(f"Industry '{lead_data.get('industry')}' matches playbook ICP")

    crm_text = _snippet_text(partitions[CRM_SOURCE])
    if partitions[CRM_SOURCE]:
        signals.append("CRM account context available")
        patterns.append("Named account — CRM enrichment used")
        if "strong icp" in crm_text:
            score += 10
            if "Strong ICP fit" not in signals:
                signals.append("Strong ICP fit")
        if any(token in crm_text for token in ("pricing", "demo", "high intent")):
            score += 5
            signals.append("CRM notes indicate active evaluation")
    else:
        risks.append("No CRM account record retrieved")

    if partitions[PLAYBOOK_SOURCE]:
        patterns.append("Qualification playbook applied to scoring")
    else:
        risks.append("Qualification playbook not in retrieved context")

    if partitions[PRODUCT_SOURCE]:
        patterns.append("Product catalog context informs ICP fit")
    if partitions[CASE_STUDY_SOURCE]:
        score += 5
        signals.append("Relevant case study evidence")
        patterns.append("Similar customer outcomes documented")

    if industry and industry not in ICP_INDUSTRIES:
        risks.append(f"Industry outside core ICP: {lead_data.get('industry')}")
        tradeoffs.append(
            f"Non-core industry '{lead_data.get('industry')}' — scored conservatively"
        )

    if "budget" not in message and "budget" not in crm_text:
        risks.append("Budget unknown")

    if score >= 70 and "budget" not in message and "budget" not in crm_text:
        tradeoffs.append("Strong intent but budget unconfirmed — qualified with caution")

    return min(100, max(0, score)), signals, risks, patterns, tradeoffs


def _build_reasoning(
    lead_data: Dict[str, Any],
    score: int,
    qualified: bool,
    signals: List[str],
    risks: List[str],
    input_labels: List[str],
) -> str:
    company = lead_data.get("company_name") or "This lead"
    status = "qualified for the sales process" if qualified else "not yet qualified for sales"
    why_parts: List[str] = []

    if "Strong ICP fit" in signals:
        why_parts.append("closely matches our ideal customer profile")
    elif lead_data.get("industry"):
        why_parts.append(f"operates in {lead_data.get('industry')}")

    if any("Pricing" in s or "engagement" in s for s in signals):
        why_parts.append("shows buying intent in the inbound message")

    if any("CRM" in s for s in signals):
        why_parts.append("CRM context supports the assessment")

    why_clause = ", and ".join(why_parts) if why_parts else "was assessed against playbook criteria"
    context_note = f" Inputs considered: {', '.join(input_labels)}."
    risk_note = f" Key risks: {'; '.join(risks[:2])}." if risks else ""

    return (
        f"{company} {why_clause}. Score {score}/100 — {status}.{context_note}{risk_note}"
    ).strip()


def _mock_qualification(lead_data: Dict[str, Any], retrieved_context: List[Dict[str, Any]]) -> Dict[str, Any]:
    partitions = partition_qualification_context(retrieved_context)
    input_labels = available_input_labels(partitions)
    disqualified, _ = check_qualification_disqualifiers(lead_data)
    score, signals, risks, patterns, tradeoffs = _score_lead(lead_data, partitions)
    qualified_preview = (not disqualified) and score >= QUALIFICATION_THRESHOLD
    reasoning = _build_reasoning(
        lead_data,
        score,
        qualified_preview,
        signals,
        risks,
        input_labels,
    )

    raw = {
        "qualified": qualified_preview,
        "score": score,
        "disqualified": disqualified,
        "signals": signals,
        "risks": risks,
        "patterns": patterns,
        "tradeoffs": tradeoffs,
        "reasoning": reasoning,
        "reason": reasoning,
        "context_inputs": input_labels,
    }
    return apply_qualification_guardrails(raw, lead_data=lead_data)


def run_qualification_agent(state: GTMState) -> Dict[str, Any]:
    lead_data = get_lead(state)
    retrieved_context = get_retrieved_context(state)
    partitions = partition_qualification_context(retrieved_context)
    input_labels = available_input_labels(partitions)

    client = get_client()
    if not client:
        return _mock_qualification(lead_data, retrieved_context)

    context_block = format_qualification_prompt_context(lead_data, partitions)
    prompt = f"""Determine whether this B2B inbound lead should enter the sales process.

{context_block}

Use all available inputs above. Identify ICP patterns, weigh tradeoffs, then score 0-100.
Explain WHY the lead is or is not qualified — a human reviewer must understand your decision.
Suggested threshold: {QUALIFICATION_THRESHOLD} (guardrails may adjust qualified flag).

Return JSON with:
- score (integer 0-100)
- qualified (boolean — your judgment before guardrails)
- signals (array — positive indicators, e.g. "Strong ICP fit", "Pricing engagement")
- risks (array — concerns or unknowns, e.g. "Budget unknown")
- patterns (array — buying/ICP patterns identified)
- tradeoffs (array — tensions you weighed)
- reasoning (string — explain WHY, per vision §7)
"""

    result = call_json_agent(
        reasoning_system_prompt("B2B sales qualification expert"),
        prompt,
        temperature=0.3,
    )
    reasoning = str(result.get("reasoning") or result.get("reason") or "")
    raw = {
        "qualified": bool(result.get("qualified", result.get("is_qualified", False))),
        "score": int(result.get("score", 0)),
        "disqualified": bool(result.get("disqualified")),
        "signals": list(result.get("signals") or []),
        "risks": list(result.get("risks") or []),
        "patterns": list(result.get("patterns") or []),
        "tradeoffs": list(result.get("tradeoffs") or []),
        "reasoning": reasoning,
        "reason": reasoning,
        "context_inputs": input_labels,
    }
    return apply_qualification_guardrails(raw, lead_data=lead_data)
