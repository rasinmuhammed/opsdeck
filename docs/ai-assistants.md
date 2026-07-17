# Using OpsDeck With AI Coding Assistants

OpsDeck is designed to work well in agent-driven workflows. If you use Codex, Cursor, Claude Code, Aider, or any IDE assistant, the fastest path to good results is to give the model a precise prompt and a small amount of application context.

## What to tell your assistant

Good prompt:

```text
Add OpsDeck to this FastAPI app.
Use the existing async SQLAlchemy engine and models.
Register User, Organization, and Invoice.
Require admin login with my AdminUser model.
Scope Invoice visibility by organization for non-superusers.
Add filters for status and created_at.
Do not introduce Node.js or frontend build tooling.
```

This works well because it tells the assistant:

- which framework you use
- which ORM path to stay on
- which models matter
- what permissions and scoping are required
- what not to add

## Prompts that work well

### 1. Add a first admin

```text
Add OpsDeck to this project using the existing async SQLAlchemy engine.
Auto-discover models from Base.
Mount it at /admin.
Keep the integration minimal and production-safe.
```

### 2. Add a serious admin

```text
Integrate OpsDeck using ModelAdmin classes instead of only register().
Use AdminUser for authentication and AdminAuditLog for audit history.
Give Users and Organizations full CRUD to admins.
Scope invoices and tickets by the current user's organization.
Add list columns, search fields, filter fields, and CSV export.
```

### 3. Add a tenant-safe admin

```text
Add OpsDeck to this multi-tenant FastAPI app.
Use row_scope so non-superusers only see records from their organization.
Protect all admin routes with the existing AdminUser auth model.
Add bulk actions only where permissions allow them.
```

## How to keep agent output high quality

- Point the assistant at the docs pages most relevant to the task.
- Prefer `ModelAdmin` once your requirements include permissions or scoping.
- Tell the assistant to reuse your existing SQLAlchemy models and auth model.
- Tell it to keep the integration FastAPI-native and not add extra admin infrastructure.

## Docs to reference in prompts

- [Getting Started](guide/getting-started.md)
- [Configuration](guide/configuration.md)
- [Integrations](guide/integrations.md)
- [API Reference](api.md)
- [FAQ](faq.md)

## Recommendation for IDEs and AI agents

If an assistant supports project docs indexing, make sure it can see:

- `README.md`
- `docs/llms.txt`
- `docs/llms-full.txt`
- the `docs/guide/` pages

Those files give the assistant the best picture of OpsDeck's intended stack and integration style.
