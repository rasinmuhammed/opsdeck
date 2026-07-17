# API Reference

## `OpsDeck`

Main entrypoint for integrating the admin into a FastAPI app.

### Constructor

```python
OpsDeck(
    app,
    secret_key,
    *,
    engine=None,
    title="Admin",
    prefix="/admin",
    templates_dir=None,
    add_csp_middleware=True,
    max_recursion_depth=5,
    auth_model=None,
    audit_model=None,
    demo_mode=False,
    secure_cookies=None,
)
```

### Key arguments

- `engine`: async SQLAlchemy engine for database-backed admin features
- `auth_model`: admin user model used for login and permission checks
- `audit_model`: concrete audit log model to persist change history
- `secure_cookies`: override secure-cookie behavior directly; otherwise use `ADMIN_SECURE_COOKIES`

### Key methods

- `register(model, **options)`: quick registration path
- `add_view(ModelAdminSubclass)`: advanced registration path
- `auto_discover(Base, include=None, exclude=None)`: register all supported declarative models
- `get_session_dependency()`: expose the admin session dependency for custom routes

## `ModelConfig`

Stored configuration for a registered model.

Notable fields:

- `list_display`
- `searchable_fields`
- `filter_fields`
- `ordering`
- `permissions`
- `row_scope`
- `actions`
- `field_overrides`
- `widgets`
- `eager_load`
- `detail_panels`
- `menu_label`
- `menu_order`

## `ModelAdmin`

Declarative advanced configuration for a model. Useful when you need reusable admin behavior or more than a handful of `register()` options.

Example:

```python
class UserAdmin(ModelAdmin):
    model = User
    list_display = ["id", "email", "is_active"]
    permissions = {"view": ["*"], "edit": ["admin"]}
```

## `AdminAction`

Defines a custom admin action.

Fields:

- `name`
- `label`
- `handler`
- `confirmation_message`
- `bulk`
- `visible`

## `DetailPanel`

Adds custom detail content to edit/detail pages.

## `DashboardCard`

Adds custom dashboard content from application-aware renderers.
