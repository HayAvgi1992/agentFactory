"""Product Fit inputs — partition context per vision §8."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.qualification_context import (
    CASE_STUDY_SOURCE,
    PRODUCT_SOURCE,
    format_context_section,
)
from app.tools.knowledge import load_document

PRODUCT_CATALOG_SOURCE = PRODUCT_SOURCE

PRODUCT_FIT_INPUT_LABELS = {
    "lead": "Lead Information",
    "qualification": "Qualification Output",
    PRODUCT_CATALOG_SOURCE: "Product Documentation",
    CASE_STUDY_SOURCE: "Case Studies",
}

CRM_KEYWORDS = ("crm", "pipeline", "lead", "sales", "deal", "revenue", "forecast")
PM_KEYWORDS = (
    "project",
    "management",
    "collaboration",
    "task",
    "sprint",
    "team",
    "coordination",
)

PRODUCTS = {
    "Monday CRM": {
        "document_id": "monday_crm",
        "keywords": CRM_KEYWORDS,
        "default_requirements": ["Pipeline visibility", "Lead tracking"],
        "ideal_industries": ("fintech", "finance", "saas", "professional services"),
    },
    "Work Management": {
        "document_id": "work_management",
        "keywords": PM_KEYWORDS,
        "default_requirements": ["Project coordination", "Team collaboration"],
        "ideal_industries": ("saas", "e-commerce", "ecommerce", "cleantech"),
    },
}


def partition_product_fit_context(
    retrieved_context: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    partitions: Dict[str, List[Dict[str, Any]]] = {
        PRODUCT_CATALOG_SOURCE: [],
        CASE_STUDY_SOURCE: [],
    }
    for item in retrieved_context:
        source = str(item.get("source") or "")
        if source in partitions:
            partitions[source].append(item)
    return partitions


def available_product_fit_inputs(
    partitions: Dict[str, List[Dict[str, Any]]],
    *,
    has_qualification: bool,
) -> List[str]:
    labels: List[str] = [PRODUCT_FIT_INPUT_LABELS["lead"]]
    if has_qualification:
        labels.append(PRODUCT_FIT_INPUT_LABELS["qualification"])
    if partitions[PRODUCT_CATALOG_SOURCE]:
        labels.append(PRODUCT_FIT_INPUT_LABELS[PRODUCT_CATALOG_SOURCE])
    if partitions[CASE_STUDY_SOURCE]:
        labels.append(PRODUCT_FIT_INPUT_LABELS[CASE_STUDY_SOURCE])
    return labels


def _snippet_blob(items: List[Dict[str, Any]]) -> str:
    return " ".join(str(item.get("snippet") or "") for item in items).lower()


def _product_signal_scores(message: str) -> Dict[str, int]:
    text = message.lower()
    return {
        name: sum(1 for kw in cfg["keywords"] if kw in text)
        for name, cfg in PRODUCTS.items()
    }


def _case_study_boost(
    partitions: Dict[str, List[Dict[str, Any]]],
    industry: str,
) -> Dict[str, int]:
    boosts = {name: 0 for name in PRODUCTS}
    industry_lower = industry.lower()
    for item in partitions[CASE_STUDY_SOURCE]:
        snippet = str(item.get("snippet") or "").lower()
        doc_id = str(item.get("document_id") or "")
        if industry_lower and industry_lower in snippet:
            if "work management" in snippet or doc_id == "saas_case_study":
                boosts["Work Management"] += 2
            if "monday crm" in snippet or "crm" in doc_id:
                boosts["Monday CRM"] += 2
        if doc_id == "fintech_case_study":
            boosts["Monday CRM"] += 1
        if doc_id == "saas_case_study":
            boosts["Work Management"] += 1
    return boosts


def _catalog_boost(partitions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
    boosts = {name: 0 for name in PRODUCTS}
    blob = _snippet_blob(partitions[PRODUCT_CATALOG_SOURCE])
    for name, cfg in PRODUCTS.items():
        if cfg["document_id"] in blob or name.lower() in blob:
            boosts[name] += 2
    return boosts


def recommend_product_from_signals(
    lead_data: Dict[str, Any],
    qualification: Dict[str, Any],
    partitions: Dict[str, List[Dict[str, Any]]],
) -> tuple[str, List[str], List[str], List[str], List[str], float]:
    message = lead_data.get("message") or ""
    industry = (lead_data.get("industry") or "").lower()
    qual_score = int(qualification.get("score", 0))

    scores = _product_signal_scores(message)
    for name, boost in _catalog_boost(partitions).items():
        scores[name] += boost
    for name, boost in _case_study_boost(partitions, industry).items():
        scores[name] += boost

    for name, cfg in PRODUCTS.items():
        if industry in cfg["ideal_industries"]:
            scores[name] += 1

    crm_score = scores["Monday CRM"]
    pm_score = scores["Work Management"]
    patterns: List[str] = []
    tradeoffs: List[str] = []

    if crm_score:
        patterns.append(f"CRM-related language ({crm_score} signals)")
    if pm_score:
        patterns.append(f"Project-management language ({pm_score} signals)")
    if partitions[PRODUCT_CATALOG_SOURCE]:
        patterns.append("Product catalog documentation consulted")
    if partitions[CASE_STUDY_SOURCE]:
        patterns.append("Case study evidence reviewed")

    if crm_score > pm_score:
        product = "Monday CRM"
        alt = ["Work Management"]
        requirements = list(PRODUCTS["Monday CRM"]["default_requirements"])
        tradeoffs.append("Work Management viable if collaboration becomes primary need")
    elif pm_score > crm_score:
        product = "Work Management"
        alt = ["Monday CRM"]
        requirements = list(PRODUCTS["Work Management"]["default_requirements"])
        tradeoffs.append("Monday CRM viable if pipeline tracking becomes priority")
    else:
        product = "Work Management"
        alt = ["Monday CRM"]
        requirements = list(PRODUCTS["Work Management"]["default_requirements"])
        tradeoffs.append("Tie score — defaulting to Work Management for general inquiry")

    if industry == "fintech" and crm_score >= pm_score:
        requirements.append("Deal velocity tracking")
        patterns.append("Fintech industry — deal velocity matters")
        product = "Monday CRM"
        alt = ["Work Management"]

    confidence = min(0.95, 0.55 + qual_score / 250 + max(crm_score, pm_score) * 0.04)
    if partitions[CASE_STUDY_SOURCE]:
        confidence = min(0.95, confidence + 0.05)
    if partitions[PRODUCT_CATALOG_SOURCE]:
        confidence = min(0.95, confidence + 0.03)

    return product, alt, requirements, patterns, tradeoffs, round(confidence, 2)


def build_product_fit_reasoning(
    lead_data: Dict[str, Any],
    product: str,
    requirements: List[str],
    input_labels: List[str],
) -> str:
    company = lead_data.get("company_name") or "The lead"
    req_note = ", ".join(requirements[:2]) if requirements else "core capabilities"
    inputs = ", ".join(input_labels)
    if product == "Monday CRM":
        align = "align strongly with CRM capabilities"
    else:
        align = "align with project and team coordination needs"
    return (
        f"{company}'s requirements {align} ({req_note}). "
        f"Recommended {product} based on lead message, qualification output, and retrieved product context. "
        f"Inputs considered: {inputs}."
    )


def format_product_fit_prompt_context(
    lead_data: Dict[str, Any],
    qualification: Dict[str, Any],
    partitions: Dict[str, List[Dict[str, Any]]],
) -> str:
    catalog_items = partitions[PRODUCT_CATALOG_SOURCE]
    catalog_text = format_context_section("Product Documentation (retrieved)", catalog_items)
    if not catalog_items:
        crm_doc = load_document("product_catalog", "monday_crm", max_chars=600)
        wm_doc = load_document("product_catalog", "work_management", max_chars=600)
        catalog_text = "Product Documentation (reference):\n"
        if crm_doc:
            catalog_text += f"  Monday CRM: {crm_doc[:300]}...\n"
        if wm_doc:
            catalog_text += f"  Work Management: {wm_doc[:300]}..."

    sections = [
        "Lead Information:",
        f"  Company: {lead_data.get('company_name')}",
        f"  Industry: {lead_data.get('industry', 'unknown')}",
        f"  Message: {lead_data.get('message')}",
        "Qualification Output:",
        f"  Score: {qualification.get('score')}/100",
        f"  Qualified: {qualification.get('qualified')}",
        f"  Signals: {', '.join(qualification.get('signals') or []) or 'none'}",
        f"  Reasoning: {qualification.get('reasoning') or qualification.get('reason') or 'n/a'}",
        catalog_text,
        format_context_section("Case Studies", partitions[CASE_STUDY_SOURCE]),
        "",
        "Available products: Monday CRM (sales pipeline), Work Management (projects, collaboration).",
    ]
    return "\n".join(sections)
