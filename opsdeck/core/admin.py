"""
Core Admin class for FastAPI Shadcn Admin.

This is the main entry point for creating an admin interface.
It orchestrates all components: registry, security, routing, database.

Architectural Philosophy:
- Composition over inheritance (uses components, not base classes)
- Dependency injection (passed to router, not globals)
- Lazy initialization (session dependency created on demand)
- Security by default (middleware, signed tokens, CSRF)

Design Decision - Why Not Flask-Admin Style:
Flask-Admin uses blueprint discovery and automatic inheritance.
We chose explicit registration because:
1. FastAPI encourages explicit over implicit
2. Better IDE autocomplete and type checking
3. Clearer dependency graph
4. Easier to test (no magic globals)

Performance:
- Initialization: O(n) where n = registered models
- Memory: ~100KB base + 1KB per registered model
- Runtime: All lookups are O(1) dictionary access
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Type, TYPE_CHECKING, Callable
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from opsdeck.core.registry import AdminRegistry, ModelConfig
from opsdeck.core.security import URLSigner, CSPMiddleware
from opsdeck.core.integrator import SchemaWalker
from opsdeck.core.router import create_admin_router
from opsdeck.core.database import DatabaseManager
from opsdeck.core.discovery import AutoDiscovery
from opsdeck.core.views import ModelAdmin

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


# Professional logging setup
logger = logging.getLogger(__name__)


# Public API
__all__ = ["OpsDeck"]
# Package paths
PACKAGE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATICS_DIR = PACKAGE_DIR / "statics"


class OpsDeck:
    """
    The main admin interface class for FastAPI.

    Usage:
        from fastapi import FastAPI
        from opsdeck import OpsDeck

        app = FastAPI()
        admin = OpsDeck(app, secret_key="your-32-char-secret-key")

        # Register your models
        admin.register(User)
        admin.register(Content, subtypes=[TextBlock, ImageBlock])

    Args:
        app: The FastAPI application instance
        secret_key: Secret key for signing tokens (minimum 16 characters)
        engine: SQLAlchemy async engine (optional, for database integration)
        title: Admin panel title (default: "Admin")
        prefix: URL prefix for admin routes (default: "/admin")
        templates_dir: Custom templates directory (optional)
        add_csp_middleware: Whether to add CSP middleware (default: True)
        max_recursion_depth: Maximum depth for schema walking (default: 5)
    """

    def __init__(
        self,
        app: FastAPI,
        secret_key: str,
        *,
        engine: "AsyncEngine | None" = None,
        title: str = "Admin",
        prefix: str = "/admin",
        templates_dir: Path | str | None = None,
        add_csp_middleware: bool = True,
        max_recursion_depth: int = 5,
        auth_model: Type["DeclarativeBase"] | None = None,
        audit_model: Type["DeclarativeBase"] | None = None,
        demo_mode: bool = False,
        secure_cookies: bool | None = None,
        theme: str = "matrix",
    ):
        self.app = app
        self.title = title
        self.prefix = prefix.rstrip("/")
        self.auth_model = auth_model
        self.audit_model = audit_model
        self.demo_mode = demo_mode
        self.secure_cookies = secure_cookies
        self.theme = theme

        # Initialize core components
        self.registry = AdminRegistry()
        self.signer = URLSigner(secret_key)
        self.walker = SchemaWalker(max_depth=max_recursion_depth)
        self.discovery = AutoDiscovery(self.registry)

        # Initialize database manager if engine provided
        self.db_manager = DatabaseManager(engine) if engine else None
        # Auto-initialize session dependency if engine provided
        self._session_dependency: Callable | None = (
            self.db_manager.get_session if self.db_manager else None
        )

        # Setup templates
        template_dirs = [TEMPLATES_DIR]
        if templates_dir:
            template_dirs.insert(0, Path(templates_dir))

        self.templates = Jinja2Templates(directory=template_dirs)

        # Add CSP middleware if enabled
        if add_csp_middleware:
            app.add_middleware(CSPMiddleware)

        # Mount static files
        self._mount_statics()

        # Initialize audit logger
        from opsdeck.audit.models import AuditLogger

        self.audit_logger = AuditLogger(audit_model) if audit_model else None

        # Create and include router
        self._setup_router()

    def _mount_statics(self) -> None:
        """Mount static files for HTMX and Alpine.js."""
        if STATICS_DIR.exists():
            self.app.mount(
                f"{self.prefix}/static",
                StaticFiles(directory=STATICS_DIR),
                name="admin:static",
            )

    def _setup_router(self) -> None:
        """Create and include the admin router."""
        router = create_admin_router(
            registry=self.registry,
            signer=self.signer,
            walker=self.walker,
            templates=self.templates,
            prefix=self.prefix,
            title=self.title,
            session_dependency=self._session_dependency,
            audit_logger=self.audit_logger,
            auth_model=self.auth_model,
            demo_mode=self.demo_mode,
            secure_cookies=self.secure_cookies,
            theme=self.theme,
        )
        self.app.include_router(router, prefix=self.prefix)

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
        row_scope=None,
        actions=None,
        field_overrides: dict[str, dict] | None = None,
        widgets: dict[str, str] | None = None,
        query_options: dict | None = None,
        eager_load: list[str] | None = None,
        detail_panels=None,
        dashboard_cards=None,
        menu_group: str | None = None,
        menu_label: str | None = None,
        menu_order: int = 100,
        admin: ModelAdmin | type[ModelAdmin] | None = None,
    ) -> ModelConfig:
        """
        Register a model with the admin interface.

        This is the primary way to add models to the admin panel. All models
        must be explicitly registered - there is no auto-discovery.

        Args:
            model: The Pydantic or SQLAlchemy model class
            name: Display name (defaults to class name)
            subtypes: Allowed subtypes for polymorphic unions
            fields: Fields to include in forms (empty = all)
            exclude: Fields to exclude from forms
            list_display: Fields to show in list view
            searchable_fields: Fields that can be searched
            filter_fields: Fields to generate sidebar filters for
            ordering: Default ordering for lists
            icon: Icon name for sidebar
            readonly: Make model read-only

        Returns:
            ModelConfig for further customization

        Example:
            # Simple model
            admin.register(User)

            # With options
            admin.register(
                Article,
                list_display=["title", "status", "created_at"],
                searchable_fields=["title", "content"],
                exclude=["internal_notes"],
            )

            # Polymorphic model
            admin.register(
                ContentBlock,
                subtypes=[TextBlock, ImageBlock, VideoBlock],
            )
        """
        return self.registry.register(
            model,
            name=name,
            subtypes=subtypes,
            fields=fields,
            exclude=exclude,
            list_display=list_display,
            searchable_fields=searchable_fields,
            filter_fields=filter_fields,
            ordering=ordering,
            icon=icon,
            readonly=readonly,
            permissions=permissions,
            row_scope=row_scope,
            actions=actions,
            field_overrides=field_overrides,
            widgets=widgets,
            query_options=query_options,
            eager_load=eager_load,
            detail_panels=detail_panels,
            dashboard_cards=dashboard_cards,
            menu_group=menu_group,
            menu_label=menu_label,
            menu_order=menu_order,
            admin=admin,
        )

    def add_view(self, admin: ModelAdmin | type[ModelAdmin]) -> ModelConfig:
        """Register a model using a ``ModelAdmin`` subclass or instance."""
        return self.registry.add_view(admin)

    def get_registry(self) -> AdminRegistry:
        """Get the model registry."""
        return self.registry

    def get_signer(self) -> URLSigner:
        """Get the URL signer."""
        return self.signer

    def get_walker(self) -> SchemaWalker:
        """Get the schema walker."""
        return self.walker

    def get_session_dependency(
        self,
    ) -> Callable[[], AsyncGenerator["AsyncSession", None]]:
        """
        Get database session dependency for use in custom routes.

        Returns:
            Async generator function for dependency injection

        Example:
            from fastapi import Depends

            get_session = admin.get_session_dependency()

            @app.get("/custom")
            async def custom_route(session = Depends(get_session)):
                # Use session here
                pass
        """
        if not self.db_manager:
            raise RuntimeError(
                "Database engine not configured. Pass engine parameter to OpsDeck."
            )

        if self._session_dependency is None:
            self._session_dependency = self.db_manager.get_session

        return self._session_dependency

    def auto_discover(
        self,
        base: "DeclarativeBase | None" = None,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> int:
        """
        Auto-discover and register SQLAlchemy models.

        Automatically finds all models and registers them with smart defaults:
        - Infers list_display from column types
        - Detects searchable text fields
        - Sets sensible ordering (created_at desc or id desc)
        - Assigns icons based on model names

        Args:
            base: SQLAlchemy declarative base (if None, tries to auto-detect)
            include: Only register these model names (if provided)
            exclude: Skip these model names

        Returns:
            Number of models registered

        Example:
            # Discover all models
            admin.auto_discover(Base)

            # Selective discovery
            admin.auto_discover(Base, include=["User", "Article"])
            admin.auto_discover(Base, exclude=["InternalModel"])
        """
        if base is None:
            # Try to auto-detect base from registered models
            raise ValueError(
                "base parameter is required for auto_discover(). "
                "Pass your SQLAlchemy Base class."
            )

        count = self.discovery.discover_all(base, include=include, exclude=exclude)
        return count
