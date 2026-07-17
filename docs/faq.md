# FAQ

## Is this only a theme?

No. OpsDeck is a FastAPI-native admin core: permissions, row scoping, bulk actions, audit hooks, and SQLAlchemy-focused ergonomics. It ships with a clean default UI, plus an optional Matrix theme (`theme="matrix"`) for those who want it.

## Does it support SQLAlchemy?

Yes. Async SQLAlchemy is the mainline path and the primary target for new features.

## Does it work with my existing FastAPI auth model?

Yes. Pass your admin user model as `auth_model` and OpsDeck will use it for login and permission checks.

## How do I keep data tenant-safe?

Use `row_scope()` through `ModelAdmin` or `register(..., row_scope=...)` to constrain every list, export, edit, and delete query to the right slice of data.

## Do I need Node.js?

No. The project stays intentionally Python-first.

## Is it ready for production?

The project is actively being hardened for production FastAPI teams. The best way to evaluate it is:

- run the test suite
- wire your own auth and audit models
- use explicit model registration
- add row scoping where your data model needs it
