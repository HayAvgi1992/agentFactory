"""In-memory lead store for Phase 1 MVP. Persistence comes in Phase 2."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from app.schemas import AgentResults, LeadCreate, LeadResponse

_leads: Dict[int, dict] = {}
_next_id = 1


def create_and_store_lead(data: LeadCreate, results: AgentResults) -> LeadResponse:
    global _next_id
    lead_id = _next_id
    _next_id += 1

    record = {
        "id": lead_id,
        "company_name": data.company_name,
        "industry": data.industry,
        "company_size": data.company_size,
        "message": data.message,
        "created_at": datetime.utcnow(),
        "results": results,
    }
    _leads[lead_id] = record
    return _to_response(record)


def list_leads() -> List[LeadResponse]:
    return [_to_response(r) for r in sorted(_leads.values(), key=lambda x: x["id"], reverse=True)]


def get_lead(lead_id: int) -> Optional[LeadResponse]:
    record = _leads.get(lead_id)
    if not record:
        return None
    return _to_response(record)


def _to_response(record: dict) -> LeadResponse:
    return LeadResponse(
        id=record["id"],
        company_name=record["company_name"],
        industry=record.get("industry"),
        company_size=record.get("company_size"),
        message=record["message"],
        created_at=record["created_at"],
        results=record.get("results"),
    )
