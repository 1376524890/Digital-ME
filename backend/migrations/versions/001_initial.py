"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-02
"""
from collections.abc import Sequence

import pgvector
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Sessions
    op.create_table(
        "sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="active"
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_", postgresql.JSONB, default=dict),
    )

    # Plys
    op.create_table(
        "plys",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("sequence_num", sa.Integer, nullable=False),
        sa.Column("user_text", sa.Text, nullable=False),
        sa.Column("ai_response", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Structured Objects
    op.create_table(
        "structured_objects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "ply_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plys.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("exchange_core", sa.Text, nullable=False),
        sa.Column("specific_context", sa.Text, nullable=False),
        sa.Column("room_assignments", postgresql.JSONB, default=list),
        sa.Column("files_touched", postgresql.JSONB, default=list),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(384), nullable=True),
        sa.Column("confidence", sa.Float, default=1.0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Profile Snapshots
    op.create_table(
        "profile_snapshots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column("pppppi_slots", postgresql.JSONB, default=dict),
        sa.Column("bdi_model", postgresql.JSONB, default=dict),
        sa.Column("ocean_scores", postgresql.JSONB, default=dict),
        sa.Column("cognitive_errors", postgresql.JSONB, default=list),
        sa.Column("vocabulary_profile", postgresql.JSONB, default=dict),
        sa.Column("syntax_preferences", postgresql.JSONB, default=list),
        sa.Column("key_taboos", postgresql.JSONB, default=list),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Skill Files
    op.create_table(
        "skill_files",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("yaml_frontmatter", sa.Text, nullable=False),
        sa.Column("global_notes", sa.Text, nullable=False),
        sa.Column("full_content", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Create HNSW index on structured_objects embedding
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_structured_objects_embedding "
        "ON structured_objects USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade():
    op.drop_table("skill_files")
    op.drop_table("profile_snapshots")
    op.drop_table("structured_objects")
    op.drop_table("plys")
    op.drop_table("sessions")
