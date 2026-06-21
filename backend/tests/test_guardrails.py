"""Guardrail tests — rules applied after agent reasoning (vision §6)."""

from app.agents.guardrails import (
    DISQUALIFIED_SCORE_CAP,
    HUMAN_REVIEW_CONFIDENCE_THRESHOLD,
    MEETING_THRESHOLD,
    QUALIFICATION_THRESHOLD,
    apply_evaluation_guardrails,
    apply_qualification_guardrails,
    apply_recommendation_guardrails,
    check_qualification_disqualifiers,
)


def test_qualification_guardrail_enforces_threshold():
    raw = {
        "score": 55,
        "qualified": True,
        "reasoning": "Looks good",
        "signals": [],
        "risks": [],
        "patterns": [],
        "tradeoffs": [],
    }
    result = apply_qualification_guardrails(raw)
    assert result["qualified"] is False
    assert result["score"] == 55
    assert any("Guardrail" in t for t in result["tradeoffs"])


def test_qualification_guardrail_clamps_score():
    result = apply_qualification_guardrails({"score": 150, "qualified": True, "reasoning": "x"})
    assert result["score"] == 100
    assert result["qualified"] is True


def test_qualification_guardrail_disqualifies_job_seeker_on_llm_path():
    raw = {
        "score": 85,
        "qualified": True,
        "reasoning": "Strong candidate",
        "signals": ["High intent"],
        "risks": [],
        "patterns": [],
        "tradeoffs": [],
    }
    lead_data = {
        "company_name": "Unknown",
        "message": "I'm looking for a job at your company.",
        "company_size": "100",
    }
    result = apply_qualification_guardrails(raw, lead_data=lead_data)
    assert result["qualified"] is False
    assert result["disqualified"] is True
    assert result["score"] == DISQUALIFIED_SCORE_CAP
    assert any("Job-seeker" in r for r in result["risks"])


def test_check_qualification_disqualifiers():
    is_dq, risks = check_qualification_disqualifiers(
        {"message": "Please unsubscribe me from your list", "company_size": "50"}
    )
    assert is_dq is True
    assert risks


def test_evaluation_guardrail_flags_low_confidence():
    raw = {
        "confidence": HUMAN_REVIEW_CONFIDENCE_THRESHOLD - 0.1,
        "needs_human_review": False,
        "missing_information": [],
        "reasoning": "Looks fine",
    }
    result = apply_evaluation_guardrails(raw)
    assert result["needs_human_review"] is True
    assert "Guardrail" in result["reasoning"]


def test_evaluation_guardrail_flags_many_missing_fields():
    raw = {
        "confidence": 0.9,
        "needs_human_review": False,
        "missing_information": ["budget", "timeline"],
        "reasoning": "Mostly complete",
    }
    result = apply_evaluation_guardrails(raw)
    assert result["needs_human_review"] is True


def test_recommendation_guardrail_downgrades_meeting():
    qual = {"score": 60, "qualified": True}
    fit = {"confidence": 0.9}
    raw = {"next_action": "book_meeting", "reasoning": "Strong lead", "patterns": [], "tradeoffs": []}
    result = apply_recommendation_guardrails(raw, qual, fit)
    assert result["next_action"] == "send_email"
    assert any("meeting threshold" in t.lower() for t in result["tradeoffs"])


def test_recommendation_guardrail_escalates_low_fit():
    qual = {"score": 80, "qualified": True}
    fit = {"confidence": 0.5}
    raw = {"next_action": "book_meeting", "reasoning": "x", "patterns": [], "tradeoffs": []}
    result = apply_recommendation_guardrails(raw, qual, fit)
    assert result["next_action"] == "human_review"


def test_recommendation_allows_meeting_above_threshold():
    qual = {"score": MEETING_THRESHOLD + 5, "qualified": True}
    fit = {"confidence": 0.9}
    raw = {"next_action": "book_meeting", "reasoning": "x", "patterns": [], "tradeoffs": []}
    result = apply_recommendation_guardrails(raw, qual, fit)
    assert result["next_action"] == "book_meeting"
