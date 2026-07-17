"""
Advanced admin view configuration primitives.

These classes provide a more expressive configuration surface for teams that
need per-model permissions, scoped queries, custom actions, and richer UI
metadata while keeping the simple ``admin.register(Model)`` API intact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

PermissionMap = dict[str, list[str]]


@dataclass(slots=True)
class AdminAction:
    """Configures a custom row or bulk action for a model."""

    name: str
    label: str
    handler: Callable[..., Any]
    confirmation_message: str | None = None
    bulk: bool = True
    visible: Callable[..., bool] | None = None


@dataclass(slots=True)
class DetailPanel:
    """Adds custom detail content to edit/detail pages."""

    name: str
    title: str
    renderer: Callable[..., Any]


@dataclass(slots=True)
class DashboardCard:
    """Adds custom dashboard metrics or cards."""

    name: str
    label: str
    renderer: Callable[..., Any]


@dataclass(slots=True)
class ModelAdmin:
    """
    Declarative advanced configuration for a registered model.

    Subclass this for ergonomic, framework-native admin customization:

    .. code-block:: python

        class UserAdmin(ModelAdmin):
            model = User
            list_display = ["id", "email", "is_active"]
            permissions = {"view": ["*"], "edit": ["admin"]}
    """

    model: type | None = None
    name: str | None = None
    menu_label: str | None = None
    menu_group: str | None = None
    menu_order: int = 100
    icon: str = "file"
    fields: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    list_display: list[str] = field(default_factory=list)
    searchable_fields: list[str] = field(default_factory=list)
    filter_fields: list[str] = field(default_factory=list)
    ordering: list[str] = field(default_factory=list)
    readonly: bool = False
    permissions: PermissionMap = field(
        default_factory=lambda: {
            "view": ["*"],
            "create": ["admin"],
            "edit": ["admin"],
            "delete": ["admin"],
            "export": ["admin"],
        }
    )
    row_scope: Callable[..., Any] | None = None
    actions: list[AdminAction] = field(default_factory=list)
    field_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)
    widgets: dict[str, str] = field(default_factory=dict)
    query_options: dict[str, Any] = field(default_factory=dict)
    eager_load: list[str] = field(default_factory=list)
    detail_panels: list[DetailPanel] = field(default_factory=list)
    dashboard_cards: list[DashboardCard] = field(default_factory=list)

    @classmethod
    def as_config(cls, model: type | None = None) -> "ModelAdmin":
        """Materialize a subclass into a concrete config instance."""
        instance = cls()
        if model is not None:
            instance.model = model
        return instance
