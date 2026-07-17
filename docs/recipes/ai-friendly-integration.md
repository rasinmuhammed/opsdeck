# Recipe: AI-Friendly Integration

If you want OpsDeck to be easy for coding assistants to integrate into your app, structure the integration so the intent is obvious.

## Recommended pattern

1. Keep admin setup in one module.
2. Use `ModelAdmin` for anything beyond a simple demo.
3. Keep auth, audit, and row scoping explicit.
4. Name your admin classes clearly: `UserAdmin`, `InvoiceAdmin`, `TicketAdmin`.

## Example

```python
from opsdeck import OpsDeck
from .admin_views import UserAdmin, TicketAdmin

admin = OpsDeck(
    app,
    engine=engine,
    secret_key=settings.ADMIN_SECRET_KEY,
    auth_model=AdminUser,
    audit_model=AdminAuditLog,
)

admin.add_view(UserAdmin)
admin.add_view(TicketAdmin)
```

This layout gives AI assistants fewer decisions to guess at and makes maintenance easier for humans too.
