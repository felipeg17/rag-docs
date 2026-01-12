from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Designed with SQLAlchemy 2.0 style ORM in mind
# Mapped -> type annotation that tells Python the type a database column will have at runtime
# title: Mapped[str]  # This attribute will be a string
# page_count: Mapped[int | None]  # This attribute will be an int or None

# mapped_column()-> function that defines the actual database column with SQL-specific configuration
# title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
#                                   ^^^^^^^^^^  ^^^^^^^^^^^^^  ^^^^^^^^^^
#                                   SQL type    DB constraint  DB index

# page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
#           ^^^^^^^^^^^^^^^^^^                          ^^^^^^^^^^^^^
#           Python type                                 SQL constraint
#           (for mypy/IDE)                              (for database)


class Base(DeclarativeBase):
    """Base class for all database models."""

    __table_args__ = {"schema": "app"}


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Document(Base, TimestampMixin):
    """Document registry table."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    title: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(200), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    page_count: Mapped[int | None] = mapped_column(nullable=True)
    content_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False,
    )
    # metadata stored as JSONB would require: from sqlalchemy.dialects.postgresql import JSONB

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title='{self.title}')>"


class SearchInteraction(Base, TimestampMixin):
    """Search interaction history table."""

    __tablename__ = "search_interactions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    query_text: Mapped[str] = mapped_column(String, nullable=False)
    k_results: Mapped[int | None] = mapped_column(nullable=True)
    results_count: Mapped[int | None] = mapped_column(nullable=True)
    avg_similarity_score: Mapped[float | None] = mapped_column(nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(nullable=True)
    session_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<SearchInteraction(id={self.id}, document_id={self.document_id})>"


class QAInteraction(Base, TimestampMixin):
    """Question-answer interaction history table."""

    __tablename__ = "qa_interactions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(String, nullable=False)
    answer: Mapped[str] = mapped_column(String, nullable=False)
    strategy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    k_results: Mapped[int | None] = mapped_column(nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(nullable=True)
    session_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<QAInteraction(id={self.id}, document_id={self.document_id})>"
