# Migrating from fastapi-admin to FastAPI Matrix Admin

The original `fastapi-admin` library (3,800 GitHub stars) has not had a release since August 2021. It requires Tortoise ORM and Redis, and it is incompatible with SQLAlchemy and modern FastAPI versions. This guide covers the direct migration path.

## What you are migrating away from

`fastapi-admin` has three hard dependencies that do not exist in FastAPI Matrix Admin:

- **Tortoise ORM** — fastapi-admin is built exclusively on Tortoise ORM. FastAPI Matrix Admin uses async SQLAlchemy 2.x.
- **Redis** — fastapi-admin requires a running Redis instance for session management. FastAPI Matrix Admin uses itsdangerous-signed session cookies.
- **Aerich** — the Tortoise ORM migration tool. You will migrate to Alembic.

---

## Step 1: Replace the ORM

fastapi-admin uses Tortoise ORM models:

```python
# fastapi-admin (Tortoise ORM)
from tortoise import fields, models

class User(models.Model):
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=200, unique=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"
```

FastAPI Matrix Admin uses SQLAlchemy declarative models:

```python
# FastAPI Matrix Admin (SQLAlchemy 2.x)
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(200), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

---

## Step 2: Replace Redis with signed cookies

fastapi-admin required Redis for session storage:

```python
# fastapi-admin — Redis required
import aioredis
from fastapi_admin.providers.login import UsernamePasswordProvider

redis = await aioredis.create_redis_pool("redis://localhost")
await app.init(
    redis=redis,
    admin_path="/admin",
    ...
)
```

FastAPI Matrix Admin uses signed session cookies — no Redis, no external process:

```python
# FastAPI Matrix Admin — no Redis needed
from fastapi_matrix_admin import MatrixAdmin

admin = MatrixAdmin(
    app,
    engine=engine,
    secret_key="your-32-char-secret-key",  # Signs session cookies
    auth_model=AdminUser,
)
```

---

## Step 3: Replace the admin setup

fastapi-admin initialization:

```python
# fastapi-admin
from fastapi_admin.app import app as admin_app
from fastapi_admin.providers.login import UsernamePasswordProvider

@app.on_event("startup")
async def startup():
    await Tortoise.init(config=TORTOISE_ORM)
    await admin_app.init(
        admin_path="/admin",
        engine=TortoiseEngine(),
        providers=[
            UsernamePasswordProvider(
                admin_model=Admin,
                login_logo_url="...",
            )
        ],
        redis=redis,
    )
```

FastAPI Matrix Admin initialization:

```python
# FastAPI Matrix Admin
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from fastapi_matrix_admin import MatrixAdmin

app = FastAPI()
engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")

admin = MatrixAdmin(
    app,
    engine=engine,
    secret_key="your-32-char-secret-key",
    title="My Admin",
    auth_model=AdminUser,   # optional — removes auth if omitted
    audit_model=AuditLog,   # optional — enables audit logging
)

# Register models explicitly
admin.register(User)
admin.register(Product)

# Or auto-discover all models
admin.auto_discover(Base)
```

---

## Step 4: Replace the admin user model

fastapi-admin defined admin users via Tortoise ORM with a specific mixin:

```python
# fastapi-admin
from fastapi_admin.models import AbstractAdmin

class Admin(AbstractAdmin):
    last_login = fields.DatetimeField(description="Last Login", default=datetime.datetime.now)
    email = fields.CharField(max_length=200, default="")
    ...

    class Meta:
        table = "admin"
```

FastAPI Matrix Admin uses an `AdminUserMixin` for SQLAlchemy:

```python
# FastAPI Matrix Admin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String
from fastapi_matrix_admin.auth.models import AdminUserMixin

class Base(DeclarativeBase):
    pass

class AdminUser(AdminUserMixin, Base):
    __tablename__ = "admin_users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    # password_hash is provided by AdminUserMixin
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
```

---

## Step 5: Replace Aerich with Alembic

fastapi-admin used Aerich for Tortoise ORM migrations. SQLAlchemy projects use Alembic:

```bash
pip install alembic
alembic init alembic
```

Then in `alembic/env.py`:

```python
from your_app.models import Base
target_metadata = Base.metadata
```

Generate and apply the initial migration:

```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

## Step 6: Migrate your data

fastapi-admin and FastAPI Matrix Admin use completely different ORMs, so there is no automatic schema migration. Your data stays in the same database. The migration is only in the application code.

For each Tortoise ORM model:
1. Create the equivalent SQLAlchemy model
2. Ensure the `__tablename__` matches your existing table name
3. Map column types: `CharField` → `String`, `IntField` → `Integer`, `BooleanField` → `Boolean`, `DatetimeField` → `DateTime`
4. Run `alembic upgrade head` against your existing database — Alembic will detect the existing tables and only create missing ones

---

## What you gain

After migrating:

- **No Redis** — simpler infrastructure, one fewer service to run and monitor
- **Audit logging** — built-in create/update/delete audit trail via `audit_model`
- **Row-level scoping** — multi-tenant data isolation via `row_scope`
- **Many-to-many relationships** — work correctly out of the box
- **Excel export** — `.xlsx` in addition to CSV (requires `pip install openpyxl`)
- **Active maintenance** — releases and bug fixes in 2026

---

## Minimum working example after migration

```python
from fastapi import FastAPI
from sqlalchemy import String, Boolean
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from fastapi_matrix_admin import MatrixAdmin
from fastapi_matrix_admin.auth.models import AdminUserMixin
from fastapi_matrix_admin.audit.models import AuditLog

app = FastAPI()
engine = create_async_engine("sqlite+aiosqlite:///./app.db")


class Base(DeclarativeBase):
    pass


class AdminUser(AdminUserMixin, Base):
    __tablename__ = "admin_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)


class AdminAuditLog(AuditLog, Base):
    __tablename__ = "admin_audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(200), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __admin_repr__(self) -> str:
        return self.username


admin = MatrixAdmin(
    app,
    engine=engine,
    secret_key="change-me-in-production",
    title="My Admin",
    auth_model=AdminUser,
    audit_model=AdminAuditLog,
)

admin.auto_discover(Base)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

---

## Getting help

If you run into issues during migration, open an issue on GitHub with the label `migration`. Include your original Tortoise ORM model definitions and what you have converted them to.
