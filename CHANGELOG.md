# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [1.2.0] - 2026-05-18

### Added

- Added `theme` parameter to `MatrixAdmin` — `theme="matrix"` (default) keeps the existing cyberpunk aesthetic, `theme="clean"` renders a neutral white/slate professional UI with no code changes required in page templates
- Added Excel (`.xlsx`) export — XLSX button appears automatically in list view alongside CSV; requires `pip install fastapi-matrix-admin[excel]` or `pip install openpyxl`; exports with styled headers and frozen panes
- Added many-to-many relationship support — SQLAlchemy `RelationshipProperty` with a secondary table is now detected automatically, rendered as a multi-select widget in the edit form, and saved correctly on both create and update
- Added `migration-from-fastapi-admin.md` recipe — direct migration guide for the 3,800-star dead library (Tortoise ORM → SQLAlchemy, Redis removal, Aerich → Alembic, side-by-side model conversion)
- Added `openpyxl` as `[excel]` optional dependency in `pyproject.toml`

### Changed

- Rewrote `docs/comparison.md` to name specific competitor bugs with GitHub issue links (SQLAdmin #776 DetachedInstanceError, #152 M2M breakage, #799 file upload data loss; starlette-admin 5-month release silence)
- Promoted live demo link to the top of `README.md`
- Documented new features (M2M, Excel, themes) in README "What ships today" section

### Fixed

- `edit_view` now correctly separates M2M relationship values from scalar column values when building the form context, preventing `AttributeError` on models with secondary-table relationships

## [1.1.0] - 2026-03-13

### Added

- Added a richer admin extension surface with `ModelAdmin`, `AdminAction`, `DetailPanel`, and `DashboardCard`
- Added global power-user keyboard shortcuts (`/` for Search, `n` for Quick Create Modal)
- Wired Dashboard Activity Stream and Recent Logs directly to the `AuditLog` database for real-team metrics
- Added model-level permissions for `view`, `create`, `edit`, `delete`, and `export`
- Added relationship search APIs for large foreign-key datasets
- Added JSON field rendering support and detail panel rendering on record pages
- Added `ROADMAP.md`, `SUPPORT.md`, migration notes, integrations docs, FAQ-style docs, and LLM-readable docs indexes

### Changed

- Refreshed the Matrix UI shell with stronger visual identity, better typography, command-hint affordances, and a more polished operator experience
- Repositioned the project around FastAPI + async SQLAlchemy instead of generic admin breadth
- Updated docs and README to reflect the actual shipped API and current product direction
- Updated docs metadata and navigation for GitHub Pages and broader discoverability
- Bumped the package version to `1.1.0`

### Fixed

- Fixed test collection so the suite runs cleanly instead of failing during discovery
- Fixed dashboard behavior in restricted environments where `psutil.boot_time()` can raise permission errors
- Fixed list table checkbox rendering so bulk-select UI behaves correctly
- Fixed audit logging defaults by requiring an explicit audit model instead of instantiating an abstract base
- Fixed critical bug where `MatrixAdmin` failed to auto-initialize session dependency, resulting in empty list views
- Fixed demo application seeding logic and added reliable database reset for better testing
- Fixed session cookie configuration so local development and production can use different secure-cookie behavior

### Security

- Enforced configured model permissions in admin routes when authentication is enabled
- Preserved CSP, signed actions, and authenticated session flows while improving the admin surface

## [1.0.3] - 2025-12-07

### Added

- Async SQLAlchemy CRUD
- Auto-discovery
- Authentication and audit logging foundations
- Matrix-styled admin UI

[1.2.0]: https://github.com/rasinmuhammed/fastapi-matrix-admin/releases/tag/v1.2.0
[1.1.0]: https://github.com/rasinmuhammed/fastapi-matrix-admin/releases/tag/v1.1.0
[1.0.3]: https://github.com/rasinmuhammed/fastapi-matrix-admin/releases/tag/v1.0.3
