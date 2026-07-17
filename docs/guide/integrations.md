# Integrations

## Authentication

Use your own SQLAlchemy admin user model by passing `auth_model=...` to `OpsDeck`.

## Audit logging

Pass a concrete audit log model with `audit_model=...` to persist create, update, and delete events.

## Alembic

If you use admin auth or audit models, include those tables in your Alembic metadata and migration flow.

## SQLModel compatibility

SQLModel projects that expose SQLAlchemy declarative models can often use the quick registration path, but async SQLAlchemy remains the primary supported target.

## File and background workflows

Use custom `AdminAction` handlers to trigger your own storage, background jobs, or internal service calls. OpsDeck does not impose a separate job system.
