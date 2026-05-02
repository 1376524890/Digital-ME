import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_: Mapped[dict] = mapped_column(JSONB, default=dict)

    plys: Mapped[list["Ply"]] = relationship(back_populates="session")
    structured_objects: Mapped[list["StructuredObject"]] = relationship(
        back_populates="session"
    )
    profile: Mapped["ProfileSnapshot | None"] = relationship(
        back_populates="session", uselist=False
    )


class Ply(Base):
    __tablename__ = "plys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id"), nullable=False, index=True
    )
    sequence_num: Mapped[int] = mapped_column(Integer, nullable=False)
    user_text: Mapped[str] = mapped_column(Text, nullable=False)
    ai_response: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["Session"] = relationship(back_populates="plys")
    structured_object: Mapped["StructuredObject | None"] = relationship(
        back_populates="ply", uselist=False
    )


class StructuredObject(Base):
    __tablename__ = "structured_objects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    ply_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plys.id"), unique=True, nullable=False
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id"), nullable=False, index=True
    )
    exchange_core: Mapped[str] = mapped_column(Text, nullable=False)
    specific_context: Mapped[str] = mapped_column(Text, nullable=False)
    room_assignments: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    files_touched: Mapped[list[str]] = mapped_column(JSONB, default=list)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    ply: Mapped["Ply"] = relationship(back_populates="structured_object")
    session: Mapped["Session"] = relationship(back_populates="structured_objects")


class ProfileSnapshot(Base):
    __tablename__ = "profile_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id"), unique=True, nullable=False
    )
    pppppi_slots: Mapped[dict] = mapped_column(JSONB, default=dict)
    bdi_model: Mapped[dict] = mapped_column(JSONB, default=dict)
    ocean_scores: Mapped[dict] = mapped_column(JSONB, default=dict)
    cognitive_errors: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    vocabulary_profile: Mapped[dict] = mapped_column(JSONB, default=dict)
    syntax_preferences: Mapped[list[str]] = mapped_column(JSONB, default=list)
    key_taboos: Mapped[list[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    session: Mapped["Session"] = relationship(back_populates="profile")


class SkillFile(Base):
    __tablename__ = "skill_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    yaml_frontmatter: Mapped[str] = mapped_column(Text, nullable=False)
    global_notes: Mapped[str] = mapped_column(Text, nullable=False)
    full_content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
