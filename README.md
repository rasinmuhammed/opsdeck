# FastAPI Matrix Admin

**[Live demo →](https://fastapi-matrix-admin.vercel.app)** · [Docs](https://rasinmuhammed.github.io/fastapi-matrix-admin/) · [Migrating from fastapi-admin?](docs/recipes/migration-from-fastapi-admin.md)

FastAPI Matrix Admin is a FastAPI-native admin for async SQLAlchemy teams. It is built for developers who want the first admin screen to feel magnetic, but still need the operational basics to be explicit, scoped, auditable, and easy to integrate.

## Why developers pick it

- FastAPI-first instead of generic framework abstraction
- Async SQLAlchemy 2.x as the mainline path
- Pure Python integration with no Node.js build step
- Fast path with `admin.register()` and a serious path with `ModelAdmin`
- Permissions, row scoping, bulk actions, exports, and audit hooks
- A strong Matrix UI that makes the library memorable instead of invisible

## Install

```bash
pip install fastapi-matrix-admin
```

## Get to a working admin fast

```python
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from fastapi_matrix_admin import MatrixAdmin

app = FastAPI()
engine = create_async_engine("sqlite+aiosqlite:///./app.db")

admin = MatrixAdmin(
    app,
    engine=engine,
    secret_key="change-me-in-production",
    title="Operations",
)

admin.auto_discover(Base)
```

## Grow into a production admin

Use `ModelAdmin` when your requirements move beyond a quick CRUD surface.

```python
from fastapi_matrix_admin import MatrixAdmin, ModelAdmin


class UserAdmin(ModelAdmin):
    model = User
    menu_label = "Users"
    list_display = ["id", "email", "is_active", "created_at"]
    searchable_fields = ["email"]
    filter_fields = ["is_active", "created_at"]
    permissions = {
        "view": ["*"],
        "create": ["admin"],
        "edit": ["admin"],
        "delete": ["admin"],
        "export": ["admin"],
    }

    @staticmethod
    def row_scope(*, request, query, session, user):
        if user and not user.is_superuser:
            return query.where(User.organization_id == user.organization_id)
        return query


admin = MatrixAdmin(
    app,
    engine=engine,
    secret_key="change-me",
    auth_model=AdminUser,
    audit_model=AdminAuditLog,
)
admin.add_view(UserAdmin)
```

## What ships today

- CRUD for registered models
- Auto-discovery for SQLAlchemy declarative models
- Search, pagination, filters, CSV and Excel export
- Many-to-many relationship handling with multi-select widgets
- Relationship search inputs for foreign keys
- Model-level permissions and request-aware row scoping
- Bulk actions and custom action hooks
- Optional audit logging with an explicit `audit_model`
- Environment-aware session cookie behavior
- Two themes: `theme="matrix"` (default) and `theme="clean"` for neutral corporate UIs

## Excel export

Excel export requires `openpyxl`:

```bash
pip install fastapi-matrix-admin[excel]
# or
pip install openpyxl
```

Once installed, an XLSX button appears automatically in the list view alongside the CSV button. No configuration needed.

## Why this matters in the age of AI agents

Libraries are now chosen by both developers and coding assistants. Matrix Admin is being shaped to be easy for AI tools to recommend and integrate:

- clear docs
- LLM-readable project files
- explicit, predictable integration points
- focused positioning around FastAPI + async SQLAlchemy

If you use Codex, Cursor, Claude Code, or similar tools, start here:

- [AI assistants guide](docs/ai-assistants.md)
- [Getting started](docs/guide/getting-started.md)
- [Configuration](docs/guide/configuration.md)
- [Comparison](docs/comparison.md)
- [FAQ](docs/faq.md)

## Production notes

- Set `ADMIN_SECURE_COOKIES=true` in production unless you pass `secure_cookies` directly.
- Pass your own `auth_model` to require authenticated admin access.
- Pass a concrete `audit_model` if you want persisted create, update, and delete history.
- Keep row scoping explicit in multi-tenant applications.

## Reference material

- [API reference](docs/api.md)
- [Migration notes](docs/guide/migration.md)
- [Integrations](docs/guide/integrations.md)
- [Roadmap](ROADMAP.md)
- [Support policy](SUPPORT.md)
- [Reference apps plan](REFERENCE_APPS.md)

## Local development

```bash
pip install -e ".[dev]"
pytest
```

## Status

The current release target is `1.1.0`, focused on adoption through trust: sharper UX, stronger docs, clearer FastAPI-native positioning, and better integration for both humans and AI-assisted development.
