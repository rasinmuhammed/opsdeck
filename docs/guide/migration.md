# Migration Notes

## From simple `register()` usage to `ModelAdmin`

If your project only needs a few list and search settings, `admin.register()` is still the quickest option.

Move to `ModelAdmin` when you need:

- model-specific permissions
- row-level query scoping
- reusable custom actions
- detail panels
- richer menu metadata

## From generic admins

OpsDeck is intentionally opinionated toward FastAPI + async SQLAlchemy. If you are migrating from a more generic admin library, expect a narrower but more FastAPI-aware integration path:

- prefer your existing FastAPI auth model instead of a separate admin user store
- use `row_scope()` for tenant-aware visibility
- use `actions` for bulk workflows
- pass an explicit `audit_model` if you want durable change history
