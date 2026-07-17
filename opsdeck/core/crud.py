"""
CRUD Base Operations for FastAPI Shadcn Admin.

Provides async database operations for SQLAlchemy models.
"""

from __future__ import annotations

from typing import Any, Callable, Generic, Type, TypeVar, Sequence, Dict
from sqlalchemy import select, func, delete as sa_delete, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base CRUD class with async SQLAlchemy operations.

    Usage:
        class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
            pass

        crud_user = CRUDUser(User)
        users = await crud_user.list(session, page=1, per_page=25)
    """

    @staticmethod
    def _apply_query_transform(
        query: Any, query_transform: Callable[[Any], Any] | None
    ):
        """Apply an optional query transform hook."""
        return query_transform(query) if query_transform else query

    def _apply_filters(self, query: Any, filters: dict[str, Any] | None) -> Any:
        """Apply exact and operator-based filters to a SQLAlchemy query."""
        if not filters:
            return query

        conditions = []
        for raw_field, value in filters.items():
            field_name, _, operator = raw_field.partition("__")
            if not hasattr(self.model, field_name):
                continue

            column = getattr(self.model, field_name)
            if value in ("", None):
                continue

            if operator == "gte":
                conditions.append(column >= value)
            elif operator == "lte":
                conditions.append(column <= value)
            elif operator in {"contains", "icontains"}:
                conditions.append(column.ilike(f"%{value}%"))
            elif operator == "in":
                values = value if isinstance(value, list) else str(value).split(",")
                conditions.append(column.in_([v for v in values if v != ""]))
            else:
                conditions.append(column == value)

        if conditions:
            query = query.where(and_(*conditions))
        return query

    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUD object with a SQLAlchemy model.

        Args:
            model: A SQLAlchemy model class
        """
        self.model = model

    async def get(
        self,
        session: AsyncSession,
        id: Any,
        *,
        load_relationships: list[str] | None = None,
        query_transform: Callable[[Any], Any] | None = None,
    ) -> ModelType | None:
        """
        Get a single record by ID.

        Args:
            session: Database session
            id: Primary key value
            load_relationships: List of relationship names to eager load

        Returns:
            Model instance or None if not found
        """
        query = select(self.model).where(self.model.id == id)
        query = self._apply_query_transform(query, query_transform)

        # Eager load relationships to avoid N+1 queries
        if load_relationships:
            for rel in load_relationships:
                query = query.options(selectinload(getattr(self.model, rel)))

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        session: AsyncSession,
        *,
        page: int = 1,
        per_page: int = 25,
        search: str | None = None,
        search_fields: list[str] | None = None,
        filters: dict[str, Any] | None = None,  # New: Advanced Filters
        order_by: list[str] | None = None,
        load_relationships: list[str] | None = None,
        query_transform: Callable[[Any], Any] | None = None,
    ) -> tuple[Sequence[ModelType], int]:
        """
        Get a paginated list of records with filtering and sorting.

        Args:
            session: Database session
            page: Page number (1-indexed)
            per_page: Records per page
            search: Search query string
            search_fields: Fields to search (for full-text search)
            filters: Dictionary of field: value filters, supporting operators like 'field__gte'
            order_by: List of fields to order by (prefix with - for DESC)
            load_relationships: Relationships to eager load

        Returns:
            Tuple of (records, total_count)
        """
        # Base query
        query = select(self.model)
        query = self._apply_query_transform(query, query_transform)

        # Apply filters
        query = self._apply_filters(query, filters)

        # Apply search
        if search and search_fields:
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    # Use case-insensitive LIKE search
                    search_conditions.append(
                        getattr(self.model, field).ilike(f"%{search}%")
                    )
            if search_conditions:
                query = query.where(or_(*search_conditions))

        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        # Apply ordering
        if order_by:
            for order_field in order_by:
                if order_field.startswith("-"):
                    # Descending order
                    field_name = order_field[1:]
                    if hasattr(self.model, field_name):
                        query = query.order_by(getattr(self.model, field_name).desc())
                else:
                    # Ascending order
                    if hasattr(self.model, order_field):
                        query = query.order_by(getattr(self.model, order_field))

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        # Eager load relationships
        if load_relationships:
            for rel in load_relationships:
                if hasattr(self.model, rel):
                    query = query.options(selectinload(getattr(self.model, rel)))

        # Execute query
        result = await session.execute(query)
        records = result.scalars().all()

        return records, total

    async def create(
        self,
        session: AsyncSession,
        *,
        obj_in: CreateSchemaType | Dict[str, Any],
    ) -> ModelType:
        """
        Create a new record.

        Args:
            session: Database session
            obj_in: Pydantic model or dict with creation data

        Returns:
            Created model instance
        """
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump(exclude_unset=True)

        db_obj = self.model(**create_data)
        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)

        return db_obj

    async def update(
        self,
        session: AsyncSession,
        *,
        id: Any,
        obj_in: UpdateSchemaType | Dict[str, Any],
        query_transform: Callable[[Any], Any] | None = None,
    ) -> ModelType | None:
        """
        Update an existing record.

        Args:
            session: Database session
            id: Primary key value
            obj_in: Pydantic model or dict with update data

        Returns:
            Updated model instance or None if not found
        """
        db_obj = await self.get(session, id, query_transform=query_transform)
        if not db_obj:
            return None

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await session.flush()
        await session.refresh(db_obj)

        return db_obj

    async def delete(
        self,
        session: AsyncSession,
        *,
        id: Any,
        query_transform: Callable[[Any], Any] | None = None,
    ) -> bool:
        """
        Delete a record by ID.

        Args:
            session: Database session
            id: Primary key value

        Returns:
            True if deleted, False if not found
        """
        if query_transform:
            scoped_record = await self.get(session, id, query_transform=query_transform)
            if not scoped_record:
                return False

        result = await session.execute(sa_delete(self.model).where(self.model.id == id))
        await session.flush()

        return result.rowcount > 0

    async def count(
        self,
        session: AsyncSession,
        *,
        filters: Dict[str, Any] | None = None,
        query_transform: Callable[[Any], Any] | None = None,
    ) -> int:
        """
        Count total records with optional filters.

        Args:
            session: Database session
            filters: Dict of field: value filters

        Returns:
            Total count
        """
        base_query = select(self.model)
        base_query = self._apply_query_transform(base_query, query_transform)
        base_query = self._apply_filters(base_query, filters)
        query = select(func.count()).select_from(base_query.subquery())

        result = await session.execute(query)
        return result.scalar_one()

    async def bulk_delete(
        self,
        session: AsyncSession,
        *,
        ids: list[Any],
        query_transform: Callable[[Any], Any] | None = None,
    ) -> int:
        """
        Delete multiple records by IDs.

        Args:
            session: Database session
            ids: List of primary key values

        Returns:
            Number of deleted records
        """
        if query_transform:
            scoped_ids_query = self._apply_query_transform(
                select(self.model.id).where(self.model.id.in_(ids)),
                query_transform,
            )
            scoped_ids_result = await session.execute(scoped_ids_query)
            scoped_ids = list(scoped_ids_result.scalars().all())
        else:
            scoped_ids = ids

        if not scoped_ids:
            return 0

        result = await session.execute(
            sa_delete(self.model).where(self.model.id.in_(scoped_ids))
        )
        await session.flush()

        return result.rowcount
