"""
Auto-discovery module for FastAPI Shadcn Admin.

Automatically discovers and registers SQLAlchemy models with smart defaults.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Type, List

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase
    from opsdeck.core.registry import AdminRegistry


class AutoDiscovery:
    """
    Auto-discovery engine that finds and registers SQLAlchemy models.

    Features:
    - Discovers all SQLAlchemy models in the codebase
    - Infers smart defaults (list_display, searchable_fields)
    - Respects explicit configurations
    - Skips abstract models

    Usage:
        discovery = AutoDiscovery(registry, base_model)
        discovery.discover_all()
    """

    def __init__(self, registry: "AdminRegistry"):
        """
        Initialize auto-discovery.

        Args:
            registry: AdminRegistry to register models into
        """
        self.registry = registry

    def discover_all(
        self,
        base: Type["DeclarativeBase"],
        include: List[str] | None = None,
        exclude: List[str] | None = None,
    ) -> int:
        """
        Discover and register all models from a SQLAlchemy Base.

        Args:
            base: SQLAlchemy declarative base
            include: Optional list of model names to include (if set, only these)
            exclude: Optional list of model names to exclude

        Returns:
            Number of models registered
        """
        registered_count = 0

        # Get all subclasses of the base
        for model in self._get_all_models(base):
            model_name = model.__name__

            # Skip if already registered
            if self.registry.is_registered(model_name):
                continue

            # Apply include/exclude filters
            if include and model_name not in include:
                continue
            if exclude and model_name in exclude:
                continue

            # Skip abstract models
            if getattr(model, "__abstract__", False):
                continue

            # Skip models without __tablename__
            if not hasattr(model, "__tablename__"):
                continue

            # Register with smart defaults
            self._register_with_defaults(model)
            registered_count += 1

        return registered_count

    def _get_all_models(self, base: Type["DeclarativeBase"]) -> List[Type]:
        """
        Get all model classes that inherit from the base.

        Args:
            base: SQLAlchemy declarative base

        Returns:
            List of model classes
        """
        models = []

        # Get all subclasses recursively
        def get_subclasses(cls):
            for subclass in cls.__subclasses__():
                if subclass not in models:
                    models.append(subclass)
                get_subclasses(subclass)

        get_subclasses(base)
        return models

    def _register_with_defaults(self, model: Type) -> None:
        """
        Register a model with smart defaults.

        Args:
            model: SQLAlchemy model class
        """
        # Infer list_display (first 5 columns)
        list_display = self._infer_list_display(model)

        # Infer searchable fields (text/varchar columns)
        searchable_fields = self._infer_searchable_fields(model)

        # Infer ordering (created_at desc if exists, else id desc)
        ordering = self._infer_ordering(model)

        # Register the model
        self.registry.register(
            model,
            list_display=list_display,
            searchable_fields=searchable_fields,
            ordering=ordering,
            icon=self._infer_icon(model),
        )

    def _infer_list_display(self, model: Type) -> List[str]:
        """
        Infer which fields to display in list view.

        Strategy:
        1. Always include 'id' if it exists
        2. Add up to 4 more fields
        3. Prefer: name, title, status, email, username
        4. Fallback to first non-relation fields

        Args:
            model: SQLAlchemy model

        Returns:
            List of field names
        """
        fields = []

        # Always start with id
        if hasattr(model, "id"):
            fields.append("id")

        # Preferred field names
        preferred = ["name", "title", "username", "email", "status", "is_active"]

        # Add preferred fields if they exist
        for field_name in preferred:
            if hasattr(model, field_name) and field_name not in fields:
                fields.append(field_name)
                if len(fields) >= 5:
                    break

        # If still need more, add timestamp fields
        if len(fields) < 5:
            timestamp_fields = ["created_at", "updated_at", "published_at"]
            for field_name in timestamp_fields:
                if hasattr(model, field_name) and field_name not in fields:
                    fields.append(field_name)
                    if len(fields) >= 5:
                        break

        # If still need more, add any other fields
        if len(fields) < 5:
            for column in model.__table__.columns:
                field_name = column.name
                if field_name not in fields:
                    # Skip long text fields (probably not good for list view)
                    if (
                        hasattr(column.type, "length")
                        and column.type.length
                        and column.type.length > 255
                    ):
                        continue
                    fields.append(field_name)
                    if len(fields) >= 5:
                        break

        return fields[:5]  # Maximum 5 fields

    def _infer_searchable_fields(self, model: Type) -> List[str]:
        """
        Infer which fields should be searchable.

        Strategy: Include all String/Text fields

        Args:
            model: SQLAlchemy model

        Returns:
            List of searchable field names
        """
        searchable = []

        for column in model.__table__.columns:
            # Check if it's a text-based column
            column_type = str(column.type).upper()
            if any(t in column_type for t in ["VARCHAR", "TEXT", "STRING", "CHAR"]):
                searchable.append(column.name)

        return searchable

    def _infer_ordering(self, model: Type) -> List[str]:
        """
        Infer default ordering.

        Strategy:
        1. If has created_at/updated_at, use descending
        2. Otherwise use id descending

        Args:
            model: SQLAlchemy model

        Returns:
            List of ordering field names (prefix - for DESC)
        """
        # Prefer created_at or updated_at descending
        for field_name in ["created_at", "updated_at", "published_at"]:
            if hasattr(model, field_name):
                return [f"-{field_name}"]

        # Fallback to id descending
        return ["-id"]

    def _infer_icon(self, model: Type) -> str:
        """
        Infer an icon for the model based on its name.

        Args:
            model: SQLAlchemy model

        Returns:
            Icon name (for display)
        """
        model_name = model.__name__.lower()

        # Icon mapping
        icon_map = {
            "user": "users",
            "admin": "shield",
            "article": "file-text",
            "post": "file-text",
            "blog": "book",
            "comment": "message-square",
            "category": "folder",
            "tag": "tag",
            "product": "shopping-cart",
            "order": "shopping-bag",
            "customer": "user",
            "payment": "credit-card",
            "invoice": "file-text",
            "setting": "settings",
            "log": "list",
            "audit": "eye",
        }

        # Check for matches
        for keyword, icon in icon_map.items():
            if keyword in model_name:
                return icon

        # Default icon
        return "database"
