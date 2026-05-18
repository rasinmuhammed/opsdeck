# Comparison: FastAPI Admin Panels

This page compares FastAPI Matrix Admin against the other Python admin panel libraries. It names specific issues, not just philosophical differences. If you are choosing an admin panel, you deserve a direct comparison.

## The short answer

| | Matrix Admin | SQLAdmin | starlette-admin | fastapi-admin |
|---|---|---|---|---|
| **Status** | Active | Active | Stalling | Dead (2021) |
| **FastAPI-native** | Yes | Yes | Yes | Yes |
| **Async SQLAlchemy** | Yes (native) | Yes (buggy) | Yes | No (Tortoise ORM) |
| **Audit logging** | Built-in | No | No | No |
| **Row-level scoping** | Built-in | No | No | No |
| **Many-to-many** | Yes | Broken | Yes | No |
| **Excel export** | Yes | No | Yes | No |
| **CSV export** | Yes | No | Yes | No |
| **Multi-tenancy** | Yes (`row_scope`) | No | No | No |
| **Build step required** | No | No | No | No |
| **Redis required** | No | No | No | Yes |
| **Neutral theme** | Yes (`theme="clean"`) | Yes (Tabler) | Yes (Tabler) | Yes |
| **Python** | 3.10+ | 3.8+ | 3.8+ | 3.8+ |

---

## SQLAdmin

**GitHub:** [smithyhq/sqladmin](https://github.com/smithyhq/sqladmin)
**PyPI downloads:** ~198,000/week
**Status:** Active, but recently transferred from original maintainer

### What SQLAdmin does well

- Broad SQLAlchemy support (sync and async, both ORM and SQLModel)
- Largest user base in the FastAPI ecosystem
- Battle-tested over many releases

### Known bugs and limitations (with sources)

**Async session `DetachedInstanceError`** — When using `async with session as s:` patterns, SQLAdmin's async session handling can raise `DetachedInstanceError` on relationship access after session close. This is a documented issue ([#776](https://github.com/aminalaee/sqladmin/issues/776)) that has been open since 2023.

**Many-to-many relationships are unreliable** — M2M support has had open issues since 2022 ([#152](https://github.com/aminalaee/sqladmin/issues/152)) and continues to surface in new bug reports. It is one of the most common pain points cited by SQLAdmin users.

**File upload corruption on edit** — When editing a record with a file field and not uploading a new file, the existing file reference is silently cleared ([#799](https://github.com/aminalaee/sqladmin/issues/799)). This is a silent data loss bug.

**No audit logging** — There is no built-in audit trail. You must instrument every create, update, and delete operation yourself.

**No row-level scoping** — There is no built-in mechanism for multi-tenant data isolation. Every admin user sees every record by default.

**No Excel export** — Data export is not a built-in feature.

**Dated UI** — The Tabler-based UI has not been substantially updated since 2022.

**Maintainer transfer** — The project was transferred from `aminalaee` to the `smithyhq` org. The long-term maintenance direction is unclear.

### Choose SQLAdmin when

- You need the widest possible community (most Stack Overflow answers, most third-party guides)
- You are using SQLModel and want first-class support
- You accept working around its async session bugs

---

## starlette-admin

**GitHub:** [jowilf/starlette-admin](https://github.com/jowilf/starlette-admin)
**PyPI downloads:** ~44,000/week
**Status:** Stalling — last release December 2025, 78 open issues as of May 2026

### What starlette-admin does well

- Broadest ORM support: SQLAlchemy, SQLModel, MongoEngine, ODMantic
- Export to CSV, Excel, PDF, and print
- Internationalization support
- DataTables integration
- Most feature-complete non-Django Python admin

### Limitations

**Release cadence has stopped** — No release since December 2025 (5+ months as of May 2026). The maintainer has not responded to open issues. This raises legitimate concerns about project health.

**Heavy frontend dependencies** — jQuery, DataTables, Select2, flatpickr, moment, TinyMCE, fontawesome. This is significant page weight and multiple external CDN dependencies.

**No audit logging** — No built-in audit trail.

**No row-level scoping** — No multi-tenant data isolation.

### Choose starlette-admin when

- You need MongoDB support (MongoEngine/ODMantic)
- You need PDF/print export
- You need internationalization
- You are comfortable accepting the maintenance risk

---

## fastapi-admin (the original)

**GitHub:** [fastapi-admin/fastapi-admin](https://github.com/fastapi-admin/fastapi-admin)
**PyPI downloads:** ~8,500/week (legacy projects on autopilot)
**Status:** Dead — last release August 2021, no active maintenance

This library has 3,800 GitHub stars accumulated over its active period and continues to appear in search results. Do not use it for new projects.

### Why it is dead

- **Tortoise ORM only** — Not compatible with SQLAlchemy. This rules it out for the majority of FastAPI projects.
- **Redis required** — Even a trivial demo requires a running Redis instance.
- **5 years without a release** — Security issues, Python version incompatibilities, and FastAPI API changes are all unaddressed.
- **61 open issues** — Including security-relevant bugs with no maintainer response.

### Migrating from fastapi-admin

See the [migration guide](recipes/migration-from-fastapi-admin.md) for a direct path from fastapi-admin to FastAPI Matrix Admin.

---

## FastAPI Matrix Admin positioning

FastAPI Matrix Admin is not trying to be the admin with the most features. It is the best admin for FastAPI teams that need audit logging, multi-tenant data isolation, and correct async SQLAlchemy behavior.

**Where it wins outright:**

1. **Audit logging** — Built-in, explicit, configurable. No other actively-maintained FastAPI admin has this.
2. **Row-level scoping** — `row_scope` isolates data by organization, tenant, or role at the query level.
3. **Many-to-many without bugs** — M2M relationships work correctly and are pre-populated on edit.
4. **Async session correctness** — Built from scratch for SQLAlchemy 2.x async. No retrofitted sync patterns.
5. **Theme choice** — `theme="matrix"` for a distinctive UI, `theme="clean"` for a neutral corporate interface.
6. **Excel export** — `.xlsx` export with styled headers alongside CSV.

**Where it is still catching up:**

- File/image upload (planned)
- MongoDB support (out of scope — SQLAlchemy only by design)
- Community size and third-party guides

If you need the largest community, use SQLAdmin and work around its bugs. If you need audit logging and multi-tenant isolation, FastAPI Matrix Admin is the only option in the Python ecosystem.
