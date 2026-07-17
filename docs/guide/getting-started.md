# Getting Started

## Install

```bash
pip install opsdeck
```

## Basic setup

```python
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from opsdeck import OpsDeck

app = FastAPI()
engine = create_async_engine("sqlite+aiosqlite:///./app.db")

admin = OpsDeck(
    app,
    engine=engine,
    secret_key="change-me-in-production",
    title="Operations",
)
```

## Register models

### Fast path

```python
admin.auto_discover(Base)
```

### Explicit path

```python
admin.register(
    User,
    list_display=["id", "email", "is_active"],
    searchable_fields=["email"],
    filter_fields=["is_active", "created_at"],
)
```

### Advanced path with `ModelAdmin`

```python
from opsdeck import ModelAdmin


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


admin.add_view(UserAdmin)
```

## Authentication

If you pass `auth_model=YourAdminUserModel`, admin routes require authenticated users. Permissions are evaluated from each model config.

```python
admin = OpsDeck(
    app,
    engine=engine,
    secret_key="change-me",
    auth_model=AdminUser,
    audit_model=AdminAuditLog,
)
```

Set `ADMIN_SECURE_COOKIES=true` in production so session cookies are marked `Secure`.

## Run locally

```bash
uvicorn main:app --reload
```

Open `http://localhost:8000/admin`.
