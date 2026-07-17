# Recipe: Multi-Tenant Row Scoping

If your app is multi-tenant, row scoping is one of the most important OpsDeck features.

```python
from opsdeck import ModelAdmin


class InvoiceAdmin(ModelAdmin):
    model = Invoice
    list_display = ["id", "customer_id", "status", "created_at"]
    searchable_fields = ["id"]
    filter_fields = ["status", "created_at"]

    @staticmethod
    def row_scope(*, request, query, session, user):
        if user is None or user.is_superuser:
            return query
        return query.where(Invoice.organization_id == user.organization_id)
```

## What row scoping affects

- list views
- export queries
- edit lookups
- delete lookups
- bulk actions

That means the same scoping rule follows the whole operator flow instead of only the first page load.
