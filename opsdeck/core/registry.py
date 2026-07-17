"""
Model Registry for FastAPI Shadcn Admin.

Provides type-safe model registration and validation with support for
polymorphic models (Pydantic discriminated unions).

Architectural Decision:
We use a centralized registry instead of decorators because:
1. Explicit registration makes dependencies clear
2. Allows runtime model discovery (auto_discover)
3. Enables strict validation before route binding
4. Supports both Pydantic and SQLAlchemy models

Security:
Registry acts as a whitelist, preventing unauthorized model access.
This is critical for preventing IDOR and information disclosure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Type, TYPE_CHECKING

from pydantic import BaseModel

from opsdeck.core.views import (
    AdminAction,
    DashboardCard,
    DetailPanel,
    ModelAdmin,
)

# Public API
__all__ = [
    "ModelConfig",
    "AdminRegistry",
    "ModelNotFoundError",
    "SubtypeNotAllowedError",
]

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase


class RegistryError(Exception):
    """Raised when registry operations fail."""

    pass


class ModelNotFoundError(RegistryError):
    """Raised when a model is not found in the registry."""

    pass


class SubtypeNotAllowedError(RegistryError):
    """Raised when attempting to use an unregistered subtype."""

    pass


@dataclass
class ModelConfig:
    """
    Configuration for a registered model.

    Attributes:
        model: The Pydantic model or SQLAlchemy model class
        name: Display name for the model (defaults to class name)
        subtypes: List of allowed subtypes for polymorphic models
        fields: List of field names to include (empty = all)
        exclude: List of field names to exclude
        list_display: Fields to show in list view
        searchable_fields: Fields that can be searched
        ordering: Default ordering fields
        icon: Optional icon name for the sidebar
        readonly: Whether the model is read-only
    """

    model: Type[BaseModel] | Type["DeclarativeBase"]
    name: str = ""
    subtypes: list[Type[BaseModel]] = field(default_factory=list)
    fields: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    list_display: list[str] = field(default_factory=list)
    searchable_fields: list[str] = field(default_factory=list)
    filter_fields: list[str] = field(default_factory=list)  # New: Advanced Filters
    ordering: list[str] = field(default_factory=list)
    icon: str = "file"
    readonly: bool = False
    permissions: dict[str, list[str]] = field(
        default_factory=lambda: {
            "view": ["*"],
            "create": ["admin"],
            "edit": ["admin"],
            "delete": ["admin"],
            "export": ["admin"],
        }
    )
    row_scope: Any = None
    actions: list[AdminAction] = field(default_factory=list)
    field_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)
    widgets: dict[str, str] = field(default_factory=dict)
    query_options: dict[str, Any] = field(default_factory=dict)
    eager_load: list[str] = field(default_factory=list)
    detail_panels: list[DetailPanel] = field(default_factory=list)
    dashboard_cards: list[DashboardCard] = field(default_factory=list)
    menu_group: str | None = None
    menu_label: str | None = None
    menu_order: int = 100

    # Internal fields
    _subtype_names: set[str] = field(default_factory=set, init=False, repr=False)

    def __post_init__(self):
        """Initialize derived fields."""
        if not self.name:
            self.name = self.model.__name__

        # Build subtype name set for fast lookup
        self._subtype_names = {st.__name__ for st in self.subtypes}

    def is_subtype_allowed(self, subtype_name: str) -> bool:
        """
        Check if a subtype is allowed for this model.

        Args:
            subtype_name: Name of the subtype to check

        Returns:
            True if the subtype is allowed
        """
        # If no subtypes defined, no subtypes are allowed
        if not self.subtypes:
            return False
        return subtype_name in self._subtype_names

    def get_subtype_class(self, subtype_name: str) -> Type[BaseModel]:
        """
        Get the subtype class by name.

        Args:
            subtype_name: Name of the subtype

        Returns:
            The subtype class

        Raises:
            SubtypeNotAllowedError: If subtype is not registered
        """
        for subtype in self.subtypes:
            if subtype.__name__ == subtype_name:
                return subtype
        raise SubtypeNotAllowedError(
            f"Subtype '{subtype_name}' is not registered for model '{self.name}'"
        )


class AdminRegistry:
    """
    Strict model registry that requires explicit registration.

    Unlike auto-discovery systems, this registry forces developers to
    explicitly register each model, preventing accidental exposure of
    sensitive models and enabling fine-grained access control.

    Usage:
        registry = AdminRegistry()
        registry.register(User, list_display=["id", "name", "email"])
        registry.register(Content, subtypes=[TextBlock, ImageBlock])

        # Get a registered model
        config = registry.get("User")

        # Validate subtype access
        if not config.is_subtype_allowed("VideoBlock"):
            raise SecurityError("Subtype not allowed")
    """

    def __init__(self):
        """Initialize an empty registry."""
        self._models: dict[str, ModelConfig] = {}

    def register(
        self,
        model: Type[BaseModel] | Type["DeclarativeBase"],
        *,
        name: str | None = None,
        subtypes: list[Type[BaseModel]] | None = None,
        fields: list[str] | None = None,
        exclude: list[str] | None = None,
        list_display: list[str] | None = None,
        searchable_fields: list[str] | None = None,
        filter_fields: list[str] | None = None,
        ordering: list[str] | None = None,
        icon: str = "file",
        readonly: bool = False,
        permissions: dict[str, list[str]] | None = None,
        row_scope: Any = None,
        actions: list[AdminAction] | None = None,
        field_overrides: dict[str, dict[str, Any]] | None = None,
        widgets: dict[str, str] | None = None,
        query_options: dict[str, Any] | None = None,
        eager_load: list[str] | None = None,
        detail_panels: list[DetailPanel] | None = None,
        dashboard_cards: list[DashboardCard] | None = None,
        menu_group: str | None = None,
        menu_label: str | None = None,
        menu_order: int = 100,
        admin: ModelAdmin | type[ModelAdmin] | None = None,
    ) -> ModelConfig:
        """
        Register a model with the admin.

        Args:
            model: The Pydantic or SQLAlchemy model class
            name: Display name (defaults to class name)
            subtypes: Allowed subtypes for polymorphic unions
            fields: Fields to include (empty = all)
            exclude: Fields to exclude
            list_display: Fields for list view
            searchable_fields: Searchable fields
            ordering: Default ordering
            icon: Sidebar icon name
            readonly: Make model read-only

        Returns:
            The ModelConfig for chaining

        Raises:
            RegistryError: If model is already registered
        """
        if admin is not None:
            admin_config = admin.as_config(model) if isinstance(admin, type) else admin
            model = admin_config.model or model
            name = name or admin_config.name
            fields = fields or admin_config.fields
            exclude = exclude or admin_config.exclude
            list_display = list_display or admin_config.list_display
            searchable_fields = searchable_fields or admin_config.searchable_fields
            filter_fields = filter_fields or admin_config.filter_fields
            ordering = ordering or admin_config.ordering
            icon = admin_config.icon or icon
            readonly = readonly or admin_config.readonly
            permissions = permissions or admin_config.permissions
            row_scope = row_scope or admin_config.row_scope
            actions = actions or admin_config.actions
            field_overrides = field_overrides or admin_config.field_overrides
            widgets = widgets or admin_config.widgets
            query_options = query_options or admin_config.query_options
            eager_load = eager_load or admin_config.eager_load
            detail_panels = detail_panels or admin_config.detail_panels
            dashboard_cards = dashboard_cards or admin_config.dashboard_cards
            menu_group = menu_group or admin_config.menu_group
            menu_label = menu_label or admin_config.menu_label
            menu_order = admin_config.menu_order

        model_name = name or model.__name__

        if model_name in self._models:
            raise RegistryError(f"Model '{model_name}' is already registered")

        config = ModelConfig(
            model=model,
            name=model_name,
            subtypes=subtypes or [],
            fields=fields or [],
            exclude=exclude or [],
            list_display=list_display or [],
            searchable_fields=searchable_fields or [],
            filter_fields=filter_fields or [],
            ordering=ordering or [],
            icon=icon,
            readonly=readonly,
            permissions=permissions
            or {
                "view": ["*"],
                "create": ["admin"],
                "edit": ["admin"],
                "delete": ["admin"],
                "export": ["admin"],
            },
            row_scope=row_scope,
            actions=actions or [],
            field_overrides=field_overrides or {},
            widgets=widgets or {},
            query_options=query_options or {},
            eager_load=eager_load or [],
            detail_panels=detail_panels or [],
            dashboard_cards=dashboard_cards or [],
            menu_group=menu_group,
            menu_label=menu_label or model_name,
            menu_order=menu_order,
        )

        self._models[model_name] = config
        return config

    def add_view(self, admin: ModelAdmin | type[ModelAdmin]) -> ModelConfig:
        """Register a model using a ModelAdmin subclass or instance."""
        admin_config = admin.as_config() if isinstance(admin, type) else admin
        if admin_config.model is None:
            raise RegistryError("ModelAdmin must define a model")
        return self.register(admin_config.model, admin=admin_config)

    def get(self, name: str) -> ModelConfig:
        """
        Get a registered model by name.

        Args:
            name: The model name

        Returns:
            The ModelConfig

        Raises:
            ModelNotFoundError: If model is not registered
        """
        if name not in self._models:
            raise ModelNotFoundError(f"Model '{name}' is not registered")
        return self._models[name]

    def get_or_none(self, name: str) -> ModelConfig | None:
        """
        Get a registered model or None if not found.

        Args:
            name: The model name

        Returns:
            The ModelConfig or None
        """
        return self._models.get(name)

    def is_registered(self, name: str) -> bool:
        """
        Check if a model is registered.

        Args:
            name: The model name

        Returns:
            True if registered
        """
        return name in self._models

    def all(self) -> list[ModelConfig]:
        """
        Get all registered models.

        Returns:
            List of all ModelConfigs
        """
        return list(self._models.values())

    def names(self) -> list[str]:
        """
        Get all registered model names.

        Returns:
            List of model names
        """
        return list(self._models.keys())

    def get_all(self) -> list[str]:
        """
        Get all registered model names (sorted).

        Alias for names() with deterministic ordering.

        Returns:
            Sorted list of model names for consistent UI rendering

        Note:
            Sorting ensures:
            - Deterministic ordering in dropdowns
            - Consistent test results
            - Better UX (alphabetical makes finding easier)
        """
        return sorted(self.names())

    def validate_model_access(self, model_name: str) -> ModelConfig:
        """
        Validate that a model is registered and return its config.

        This is the primary security check for request handling.

        Args:
            model_name: The model name to validate

        Returns:
            The ModelConfig if valid

        Raises:
            ModelNotFoundError: If model is not registered
        """
        return self.get(model_name)

    def validate_subtype_access(
        self, model_name: str, subtype_name: str
    ) -> Type[BaseModel]:
        """
        Validate that a subtype is allowed for a model.

        This is the security check for polymorphic form loading.

        Args:
            model_name: The parent model name
            subtype_name: The subtype to validate

        Returns:
            The subtype class if valid

        Raises:
            ModelNotFoundError: If parent model is not registered
            SubtypeNotAllowedError: If subtype is not allowed
        """
        config = self.get(model_name)
        return config.get_subtype_class(subtype_name)

    def __len__(self) -> int:
        """Return the number of registered models."""
        return len(self._models)

    def __contains__(self, name: str) -> bool:
        """Check if a model is registered."""
        return name in self._models

    def __iter__(self):
        """Iterate over registered model configs."""
        return iter(self._models.values())
