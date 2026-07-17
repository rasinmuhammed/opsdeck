# Configuration

## `OpsDeck`

```python
admin = OpsDeck(
    app,
    secret_key="change-me",
    engine=engine,
    title="Operations",
    prefix="/admin",
    auth_model=AdminUser,
    audit_model=AdminAuditLog,
    secure_cookies=True,
)
```

### Important options

- `engine`: enables database-backed CRUD, search, export, and relationship lookups
- `auth_model`: enables admin login and permission checks
- `audit_model`: persists create, update, and delete history
- `secure_cookies`: forces secure session cookies even outside environment defaults

## `register()` options

```python
admin.register(
    User,
    list_display=["id", "email"],
    searchable_fields=["email"],
    filter_fields=["is_active"],
    permissions={"view": ["*"], "edit": ["admin"]},
    eager_load=["organization"],
)
```

Common options:

- `fields`
- `exclude`
- `list_display`
- `searchable_fields`
- `filter_fields`
- `ordering`
- `readonly`
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

Use `ModelAdmin` when you want a reusable declarative config rather than a long `register()` call.

```python
class InvoiceAdmin(ModelAdmin):
    model = Invoice
    menu_label = "Invoices"
    list_display = ["id", "customer_id", "status", "created_at"]
    filter_fields = ["status", "created_at"]
    permissions = {"view": ["*"], "export": ["finance", "admin"]}
```
