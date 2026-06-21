from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    pipeline_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    pipeline_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pipeline_step_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    state_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    human_review_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    human_review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    agent_runs: Mapped[List["AgentRun"]] = relationship(
        "AgentRun",
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by="AgentRun.created_at",
    )
    experiment_runs: Mapped[List["ExperimentRun"]] = relationship(
        "ExperimentRun",
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by="ExperimentRun.created_at",
    )


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    input: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    output: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    tools_used: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    retrieved_documents: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    lead: Mapped["Lead"] = relationship("Lead", back_populates="agent_runs")


class PromptVersion(Base):
    """Prompt templates — vision §15 / §17."""

    __tablename__ = "prompt_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )


class ExperimentRun(Base):
    """A/B prompt comparison — vision §15–16 / §17."""

    __tablename__ = "experiment_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    version_a: Mapped[str] = mapped_column(String(32), nullable=False)
    version_b: Mapped[str] = mapped_column(String(32), nullable=False)
    result_a: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    result_b: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    winner: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    metrics: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    lead: Mapped["Lead"] = relationship("Lead", back_populates="experiment_runs")
