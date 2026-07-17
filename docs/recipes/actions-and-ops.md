# Recipe: Bulk Actions And Operator Workflows

Bulk actions are a good fit for real backoffice work: moderation, triage, approval, and cleanup flows.

```python
from opsdeck import AdminAction, ModelAdmin


async def approve_invoices(*, request, session, model, ids, user, config):
    await session.execute(
        model.__table__.update()
        .where(model.id.in_(ids))
        .values(status="approved")
    )
    return {"ok": True, "approved": len(ids)}


class InvoiceAdmin(ModelAdmin):
    model = Invoice
    actions = [
        AdminAction(
            name="approve_invoices",
            label="Approve invoices",
            handler=approve_invoices,
        )
    ]
```

## When to use custom actions

- status transitions
- retrying failed jobs
- content moderation
- support tooling
- finance and operations approvals

Keep actions small, explicit, and audit-friendly.
