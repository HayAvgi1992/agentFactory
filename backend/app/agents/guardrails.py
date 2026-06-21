"""Business-rule guardrails — applied after agent reasoning (vision §6).

Rules define guardrails. LLMs perform reasoning. These functions enforce thresholds
and valid ranges without replacing the agent's explanatory output.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.agents.qualification_context import parse_employee_count

QUALIFICATION_THRESHOLD = 60
MEETING_THRESHOLD = 75
HUMAN_REVIEW_FIT_THRESHOLD = 0.65
HUMAN_REVIEW_CONFIDENCE_THRESHOLD = 0.6
DISQUALIFIED_SCORE_CAP = 15
VALID_ACTIONS = frozenset({"book_meeting", "send_email", "nurture", "reject", "human_review"})

_JOB_SEEKER_PHRASES = ("looking for a job", "job application", "send my resume", "hiring manager")
_SPAM_PHRASES = ("unsubscribe", "buy our list", "seo services")
_COMPETITOR_PHRASES = ("competitor analysis", "for research only", "not looking to buy")


def _ensure_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def check_qualification_disqualifiers(lead_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Hard disqualifiers from the qualification playbook — apply on mock and LLM paths."""
    message = (lead_data.get("message") or "").lower()
    risks: List[str] = []

    if any(p in message for p in _JOB_SEEKER_PHRASES):
        risks.append("Job-seeker inquiry — not a buying signal")
        return True, risks
    if any(p in message for p in _SPAM_PHRASES):
        risks.append("Generic spam detected")
        return True, risks
    if any(p in message for p in _COMPETITOR_PHRASES):
        risks.append("Competitor research with no buying intent")
        return True, risks

    employees = parse_employee_count(lead_data.get("company_size"))
    budget_signal = any(
        token in message for token in ("budget", "pricing", "demo", "cost", "purchase")
    )
    if employees is not None and employees < 10 and not budget_signal:
        risks.append("Company under 10 employees with no budget signal")
        return True, risks
    return False, risks


def apply_qualification_guardrails(
    output: Dict[str, Any],
    *,
    lead_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    score = int(output.get("score", 0))
    score = max(0, min(100, score))

    reasoning = output.get("reasoning") or output.get("reason") or ""
    guardrail_notes: List[str] = _ensure_list(output.get("tradeoffs"))
    risks = _ensure_list(output.get("risks"))
    disqualified = bool(output.get("disqualified"))

    if lead_data:
        is_disqualified, disqual_risks = check_qualification_disqualifiers(lead_data)
        if is_disqualified:
            disqualified = True
            for risk in disqual_risks:
                if risk not in risks:
                    risks.append(risk)
            if score > DISQUALIFIED_SCORE_CAP:
                guardrail_notes.append(
                    f"Guardrail: score capped at {DISQUALIFIED_SCORE_CAP} (hard disqualifier)"
                )
                score = DISQUALIFIED_SCORE_CAP

    qualified = (not disqualified) and score >= QUALIFICATION_THRESHOLD

    if bool(output.get("qualified")) != qualified:
        guardrail_notes.append(
            f"Guardrail: qualified set to {qualified} "
            f"(score {score}, threshold {QUALIFICATION_THRESHOLD}"
            f"{', disqualified' if disqualified else ''})"
        )

    return {
        **output,
        "score": score,
        "qualified": qualified,
        "disqualified": disqualified,
        "reason": reasoning,
        "reasoning": reasoning,
        "signals": _ensure_list(output.get("signals")),
        "risks": risks,
        "patterns": _ensure_list(output.get("patterns")),
        "tradeoffs": guardrail_notes,
    }


def apply_product_fit_guardrails(output: Dict[str, Any]) -> Dict[str, Any]:
    confidence = float(output.get("confidence", 0.7))
    confidence = max(0.0, min(1.0, confidence))
    return {
        **output,
        "confidence": round(confidence, 2),
        "alternative_products": _ensure_list(output.get("alternative_products")),
        "matching_requirements": _ensure_list(output.get("matching_requirements")),
        "patterns": _ensure_list(output.get("patterns")),
        "tradeoffs": _ensure_list(output.get("tradeoffs")),
        "reasoning": str(output.get("reasoning") or ""),
    }


def apply_recommendation_guardrails(
    output: Dict[str, Any],
    qualification: Dict[str, Any],
    product_fit: Dict[str, Any],
) -> Dict[str, Any]:
    score = int(qualification.get("score", 0))
    qualified = bool(qualification.get("qualified"))
    fit_confidence = float(product_fit.get("confidence", 1.0))
    action = str(output.get("next_action") or output.get("action") or "send_email")
    tradeoffs = _ensure_list(output.get("tradeoffs"))

    if action not in VALID_ACTIONS:
        tradeoffs.append(f"Guardrail: invalid action '{action}' replaced with send_email")
        action = "send_email"

    if fit_confidence < HUMAN_REVIEW_FIT_THRESHOLD and qualified and action != "reject":
        tradeoffs.append(
            f"Guardrail: product-fit confidence {fit_confidence:.0%} below "
            f"{HUMAN_REVIEW_FIT_THRESHOLD:.0%} — escalated to human_review"
        )
        action = "human_review"
    elif action == "book_meeting" and score < MEETING_THRESHOLD:
        tradeoffs.append(
            f"Guardrail: score {score} below meeting threshold {MEETING_THRESHOLD} — downgraded to send_email"
        )
        action = "send_email"
    elif action in ("send_email", "book_meeting") and not qualified:
        tradeoffs.append("Guardrail: lead not qualified — downgraded to nurture")
        action = "nurture"

    return {
        **output,
        "next_action": action,
        "patterns": _ensure_list(output.get("patterns")),
        "tradeoffs": tradeoffs,
        "reasoning": str(output.get("reasoning") or ""),
    }


def apply_evaluation_guardrails(output: Dict[str, Any]) -> Dict[str, Any]:
    confidence = float(output.get("confidence", 0.7))
    confidence = max(0.0, min(1.0, confidence))
    missing = _ensure_list(output.get("missing_information"))
    needs_review = bool(output.get("needs_human_review", False))
    tradeoffs: List[str] = []

    if confidence < HUMAN_REVIEW_CONFIDENCE_THRESHOLD:
        if not needs_review:
            tradeoffs.append(
                f"Guardrail: confidence {confidence:.0%} below "
                f"{HUMAN_REVIEW_CONFIDENCE_THRESHOLD:.0%} — flagged for human review"
            )
        needs_review = True
    if len(missing) >= 2 and not needs_review:
        tradeoffs.append(
            f"Guardrail: {len(missing)} missing information fields — flagged for human review"
        )
        needs_review = True

    result = {
        **output,
        "confidence": round(confidence, 2),
        "needs_human_review": needs_review,
        "missing_information": missing,
        "reasoning": str(output.get("reasoning") or ""),
    }
    if tradeoffs:
        existing = str(result.get("reasoning") or "")
        guardrail_note = " ".join(tradeoffs)
        result["reasoning"] = f"{existing} {guardrail_note}".strip() if existing else guardrail_note
    return result
