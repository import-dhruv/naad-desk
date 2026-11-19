"""SQLAlchemy ORM models for all persisted Naad Desk entities (PRD §13)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Doctor(Base):
    __tablename__ = "doctors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    speciality: Mapped[str] = mapped_column(String(120), nullable=False)
    fee_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    languages: Mapped[str] = mapped_column(String(120), default="hi,gu,en")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Holiday(Base):
    __tablename__ = "clinic_holidays"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)  # YYYY-MM-DD
    reason: Mapped[str] = mapped_column(String(160), default="")


class Slot(Base):
    __tablename__ = "slots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    start_ts: Mapped[datetime] = mapped_column(nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[str] = mapped_column(String(20), default="available")  # available|booked|blocked
    doctor: Mapped[Doctor] = relationship()

    __table_args__ = (
        UniqueConstraint("doctor_id", "start_ts", name="uq_slot_doctor_time"),
        Index("ix_slot_start_ts", "start_ts"),
        Index("ix_slot_status", "status"),
    )


class Appointment(Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id", ondelete="RESTRICT"), nullable=False)
    patient_name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone_masked: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="confirmed")  # confirmed|cancelled
    created_call_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    slot: Mapped[Slot] = relationship()

    # One *live* appointment per slot — DB-level protection against double booking.
    # Partial unique index: cancelled rows are excluded, so a released slot can be
    # rebooked while two confirmed appointments for the same slot remain impossible.
    __table_args__ = (
        Index("uq_live_appointment_slot", "slot_id", unique=True,
              sqlite_where=(status == "confirmed")),
        Index("ix_appointment_status", "status"),
        Index("ix_appointment_call", "created_call_id"),
    )


class Call(Base):
    __tablename__ = "calls"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    language: Mapped[str] = mapped_column(String(12), default="hi")
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    kb_version: Mapped[str] = mapped_column(String(32), default="kb-v1")
    cost_paise: Mapped[int] = mapped_column(Integer, default=0)
    outcome: Mapped[str] = mapped_column(String(40), default="in_progress")
    qa_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recording_disclosure: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix_call_started", "started_at"),)


class Turn(Base):
    __tablename__ = "turns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_id: Mapped[str] = mapped_column(ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker: Mapped[str] = mapped_column(String(12), nullable=False)  # caller|agent|system
    text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(12), nullable=True)
    t_client_end_speech: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_engine_endpoint: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_transcript: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_retrieval: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_plan: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_tool: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_first_say: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_first_audio: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_first_played: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_turn_complete: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_event: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix_turn_call_idx", "call_id", "idx"),)


class ToolCall(Base):
    __tablename__ = "tool_calls"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    turn_id: Mapped[int] = mapped_column(ForeignKey("turns.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    args_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0)


class Retrieval(Base):
    __tablename__ = "retrievals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    turn_id: Mapped[int] = mapped_column(ForeignKey("turns.id", ondelete="CASCADE"), nullable=False)
    chunk_ids: Mapped[str] = mapped_column(Text, default="[]")
    scores: Mapped[str] = mapped_column(Text, default="[]")
    confidence: Mapped[float] = mapped_column(Float, default=0)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0)


class ApiCall(Base):
    __tablename__ = "api_calls"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    endpoint: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False)
    headers_json: Mapped[str] = mapped_column(Text, default="{}")
    latency_ms: Mapped[float] = mapped_column(Float, default=0)
    cost_paise: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    __table_args__ = (Index("ix_api_call_call", "call_id"),)


class Analytics(Base):
    __tablename__ = "analytics"
    call_id: Mapped[str] = mapped_column(ForeignKey("calls.id", ondelete="CASCADE"), primary_key=True)
    caller_transcript: Mapped[str] = mapped_column(Text, default="")
    agent_transcript: Mapped[str] = mapped_column(Text, default="")
    merged_transcript: Mapped[str] = mapped_column(Text, default="")
    extraction_json: Mapped[str] = mapped_column(Text, default="{}")
    qa_json: Mapped[str] = mapped_column(Text, default="{}")
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=func.now())


class Document(Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(12), nullable=False)
    title: Mapped[str] = mapped_column(String(200), default="")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    indexed_at: Mapped[datetime] = mapped_column(default=func.now())
    status: Mapped[str] = mapped_column(String(20), default="indexed")


class Chunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    section: Mapped[str] = mapped_column(String(200), default="")
    language: Mapped[str] = mapped_column(String(12), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    idx: Mapped[int] = mapped_column(Integer, default=0)
    document: Mapped[Document] = relationship()

    __table_args__ = (Index("ix_chunk_doc", "document_id"),)


class EvalRun(Base):
    __tablename__ = "eval_runs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    started_at: Mapped[datetime] = mapped_column(default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    config_json: Mapped[str] = mapped_column(Text, default="{}")
    metrics_json: Mapped[str] = mapped_column(Text, default="{}")
    git_sha: Mapped[str] = mapped_column(String(40), default="unknown")

    __table_args__ = (Index("ix_eval_kind", "kind"),)


class EvalSample(Base):
    __tablename__ = "eval_samples"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("eval_runs.id", ondelete="CASCADE"), nullable=False)
    sample_id: Mapped[str] = mapped_column(String(80), nullable=False)
    condition: Mapped[str] = mapped_column(String(60), default="clean")
    reference: Mapped[str] = mapped_column(Text, default="")
    hypothesis: Mapped[str] = mapped_column(Text, default="")
    metric: Mapped[str] = mapped_column(String(40), default="wer")
    value: Mapped[float] = mapped_column(Float, default=0)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (Index("ix_eval_sample_run", "run_id"),)


class Finding(Base):
    __tablename__ = "findings"
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # high|medium|low|suggestion
    area: Mapped[str] = mapped_column(String(80), nullable=False)
    expected: Mapped[str] = mapped_column(Text, default="")
    actual: Mapped[str] = mapped_column(Text, default="")
    reproduction_steps: Mapped[str] = mapped_column(Text, default="")
    evidence_path: Mapped[str] = mapped_column(String(255), default="")
    suggestion: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="open")
    kind: Mapped[str] = mapped_column(String(24), default="observation")  # bug|limitation|observation|improvement
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    __table_args__ = (
        Index("ix_finding_severity", "severity"),
        Index("ix_finding_area", "area"),
    )
