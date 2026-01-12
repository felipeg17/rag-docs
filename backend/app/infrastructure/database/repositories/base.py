from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import Base


# Place holder for model types (Document, QAInteraction)
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: Session, model: Type[ModelType]):
        self._session = session
        self._model = model

    def get_by_id(self, id: UUID) -> ModelType | None:
        # stmt -> SQL statement
        # SQLAlquemy 2.0 pattern
        # 1. execute(stmt) → Returns Result (raw database rows)
        # 2. .scalar_one_or_none() → Converts to Python object
        # result = session.execute(stmt)
        # result.scalar_one_or_none()  # Single object
        # result.scalars().all()       # List of objects
        # result.mappings().all()      # List of dicts

        query = select(self._model).where(self._model.id == id)  # type: ignore[attr-defined]
        # `or_none` won't raise if not found
        return self._session.execute(query).scalar_one_or_none()

    def create(self, **kwargs) -> ModelType:
        instance = self._model(**kwargs)
        self._session.add(instance)
        self._session.flush()  # Get ID without committing transaction
        return instance

    def delete(self, id: UUID) -> bool:
        instance = self.get_by_id(id)
        if instance:
            self._session.delete(instance)
            return True
        return False
