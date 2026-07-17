# Recipe: Auth And Audit Logging

Use this setup when you want a proper internal admin instead of a public CRUD surface.

```python
from opsdeck import OpsDeck

admin = OpsDeck(
    app,
    engine=engine,
    secret_key=settings.ADMIN_SECRET_KEY,
    auth_model=AdminUser,
    audit_model=AdminAuditLog,
    title="Operations",
)
```

## Why this matters

- `auth_model` turns on authenticated admin flows
- `audit_model` gives you durable create, update, and delete history
- you keep your existing SQLAlchemy user model instead of adopting a separate auth system

## Recommended additions

- set `ADMIN_SECURE_COOKIES=true` in production
- keep admin routes behind your existing ingress and environment controls
- mark sensitive models `readonly=True` if operators should inspect but not mutate them
