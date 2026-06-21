"""Qualification inputs — partition retrieved context per vision §7."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

# From knowledge/sales_playbooks/qualification.md
ICP_INDUSTRIES = frozenset(
    {"saas", "fintech", "finance", "professional services", "e-commerce", "ecommerce"}
)
PLAYBOOK_SCORING = {
    "demo_or_pricing": 20,
    "urgency": 15,
    "company_size_100_plus": 10,
    "industry_fit": 5,
}
CRM_SOURCE = "crm_accounts"
PLAYBOOK_SOURCE = "sales_playbooks"
PRODUCT_SOURCE = "product_catalog"
CASE_STUDY_SOURCE = "case_studies"

QUALIFICATION_INPUT_LABELS = {
    CRM_SOURCE: "CRM Context",
    PLAYBOOK_SOURCE: "Qualification Playbook",
    PRODUCT_SOURCE: "Product Context",
    CASE_STUDY_SOURCE: "Case Studies",
}


def parse_employee_count(company_size: str | None) -> Optional[int]:
    if not company_size:
        return None
    text = str(company_size).lower().replace(",", "")
    range_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", text)
    if range_match:
        low, high = int(range_match.group(1)), int(range_match.group(2))
        return (low + high) // 2
    digits = re.findall(r"\d+", text)
    if not digits:
        return None
    return int(digits[0])


def partition_qualification_context(
    retrieved_context: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    partitions: Dict[str, List[Dict[str, Any]]] = {
        CRM_SOURCE: [],
        PLAYBOOK_SOURCE: [],
        PRODUCT_SOURCE: [],
        CASE_STUDY_SOURCE: [],
    }
    for item in retrieved_context:
        source = str(item.get("source") or "")
        if source in partitions:
            partitions[source].append(item)
    return partitions


def available_input_labels(partitions: Dict[str, List[Dict[str, Any]]]) -> List[str]:
    labels: List[str] = ["Lead Information"]
    for source, items in partitions.items():
        if items:
            labels.append(QUALIFICATION_INPUT_LABELS[source])
    return labels


def load_playbook_excerpt(max_chars: int = 800) -> str:
    path = Path(settings.knowledge_dir) / "sales_playbooks" / "qualification.md"
    if not path.is_file():
        return "Qualification playbook unavailable."
    return path.read_text(encoding="utf-8")[:max_chars]


def format_context_section(title: str, items: List[Dict[str, Any]]) -> str:
    if not items:
        return f"{title}: (none retrieved)"
    lines = [title + ":"]
    for item in items[:3]:
        lines.append(
            f"  - [{item.get('document_id', 'doc')}] "
            f"{str(item.get('snippet', ''))[:250]}"
        )
    return "\n".join(lines)


def format_qualification_prompt_context(
    lead_data: Dict[str, Any],
    partitions: Dict[str, List[Dict[str, Any]]],
) -> str:
    playbook_items = partitions[PLAYBOOK_SOURCE]
    playbook_text = (
        format_context_section("Qualification Playbook (retrieved)", playbook_items)
        if playbook_items
        else f"Qualification Playbook (reference):\n{load_playbook_excerpt()}"
    )
    sections = [
        "Lead Information:",
        f"  Company: {lead_data.get('company_name')}",
        f"  Industry: {lead_data.get('industry', 'unknown')}",
        f"  Company Size: {lead_data.get('company_size', 'unknown')}",
        f"  Message: {lead_data.get('message')}",
        format_context_section("CRM Context", partitions[CRM_SOURCE]),
        playbook_text,
        format_context_section("Product Context", partitions[PRODUCT_SOURCE]),
        format_context_section("Case Studies", partitions[CASE_STUDY_SOURCE]),
    ]
    return "\n\n".join(sections)
