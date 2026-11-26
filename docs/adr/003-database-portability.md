# ADR 003: SQLite and PostgreSQL portability

Date: 2026-11-26
Status: accepted design; implementation scope in architecture overview.

## Context and decision
Use SQLAlchemy and SQLite for local metadata. No domain schema exists; Alembic is installed for future migrations. Add dialect-neutral migrations and PostgreSQL integration tests before claiming compatibility.

## Consequences
Lower Phase 0 operational cost; future features must satisfy the documented release gates.
