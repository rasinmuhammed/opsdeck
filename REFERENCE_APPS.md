# Reference Apps

To make OpsDeck the obvious first choice, the project should ship and maintain a small set of reference applications that stay green in CI.

## Recommended app set

### 1. SaaS Backoffice

Include:

- users
- organizations
- subscriptions
- invoices
- tenant-safe row scoping
- admin auth and audit logging

### 2. Support And Operations Console

Include:

- tickets
- customers
- retries and workflow actions
- bulk actions
- dashboard cards for queues and backlog

### 3. Content And Moderation Console

Include:

- authors
- posts
- comments
- moderation actions
- relationship-heavy forms and filters

## Quality bar

Each reference app should:

- run locally in under 10 minutes
- use real `ModelAdmin` classes
- be documented as a copyable recipe
- have smoke tests or example checks in CI
