# Project state — 2026-11-27

## Handoff
Version 0.1.0 on main. The public [repository](https://github.com/MayankYadav-ds/RetainIQ) contains the Phase 0 engineering foundation. Project service expenditure is INR 0. No public app or cloud database was provisioned. Start with the root README for installation, native runtime and checks.

## Implemented
- FastAPI factory, typed environment settings with production boundaries, JSON application logs, bounded request IDs, restricted hosts/CORS and sanitized errors. The SQLAlchemy lifecycle opens SQLite, probes it per readiness request and disposes it on shutdown.
- React/TypeScript/Vite/Tailwind shell with responsive layout, keyboard navigation, light/dark theme, planned capability labels, empty state and a real version/readiness check with timeout and retry.
- Dependency locks, format/lint/type gates, API and UI tests, production build and Chromium integration suite. Seven decisions in docs/adr record modular monolith boundaries, local-first execution, database portability, temporal evaluation, causal interpretation, deployment cost and future guest isolation.
- Product requirements, ML integrity contract, dataset research, manifest schema, threat model, recovery design and hosting strategy. No ingestion, training, intervention outcomes or customer data.

## Audit
Original workspace contained only work and outputs directories. Created an isolated RetainIQ repository. Verified Git 2.54.0, configured identity, Python 3.11.0, Node 24.19.0, npm 11.17.0 and authenticated gh 2.101.0 on Windows x64. Initial RAM 15.3 GiB visible and 3.57 GiB free, with about 725 GiB disk free. Docker CLI 29.8.2 and Compose 5.5.1 were installed. The Docker Desktop Linux engine pipe was unavailable. No security policy changes, WSL or GPU were required.

## Local validation
Validated on native Windows with the locked dependencies. The built frontend and actual API ran together on ports 4173 and 8000. A separate development startup on 5173 verified the connected UI, readiness and interactive docs. Validation servers were stopped after checks.

| Command (see scripts/check.py for working directories) | Tests | Passed | Failed | Skipped |
|---|---:|---:|---:|---:|
| python -m pytest backend/tests -q | 22 | 22 | 0 | 0 |
| npm test | 8 | 8 | 0 | 0 |
| npm run e2e | 2 | 2 | 0 | 0 |

Ruff lint and format, strict Mypy, ESLint, TypeScript and Vite build passed. Database startup failure and recovery, redaction, host and CORS checks, error correlation, loading/failure/retry and browser connectivity were exercised. Axe reported zero violations in both themes at the tested viewport and the layout passed the mobile overflow assertion. Manual assistive-technology and broad browser validation remain open. Docker Compose configuration parsed successfully. Image build/run and PostgreSQL dialect behavior remain unverified.

## Operational limits and technical debt
- Windows Application Control rejected SQLAlchemy's optional native extension. The documented pure-Python distribution of the same version passed. Starlette's TestClient emitted a deprecation warning for httpx. Review the supported successor before a future dependency upgrade.
- SQLite stores no domain tables. Introduce Alembic migrations and a tested restore before persistence. Validate PostgreSQL separately. Container base tags are mutable and the current Python image includes tooling from the development lock.
- GET-only public metadata has no authenticated tenant data. Before public tenant workflows implement identity, authorization, server-derived workspace scoping, quotas, TTL cleanup, HTTPS and proxy limits. Hosting quotas and card-free signup remain account-dependent. See docs/DEPLOYMENT_STRATEGY.md.
- Application-level logs omit sensitive fields. Keep Uvicorn raw access logging disabled at runtime and review proxy logs before handling sensitive records.

## Git and continuation
Main history through validation: efcaa0c (standards), 1d45c56 (architecture and science), c42410c (API), 3ed05d4 (UI), 338e374 (quality gates). Use git log -1 for the handoff commit. The initial push was rejected by GitHub's GH007 privacy protection. The original local commits remain on prepublication-local. Publish only main, which uses the GitHub no-reply address.

Phase 1 is ready to start when authorized. Use UCI as the first candidate, verify current license and attribution, record source/version/checksum and acquisition time, validate the manifest, profile actual columns, and audit feature availability, target window and censoring before choosing splits. KKBox requires separate account access and accepted terms. IBM sample redistribution needs a file-level rights check. No candidate has been acquired.

## Acceptance and hosted CI
**Phase 0 COMPLETE.** The standard public GitHub Ubuntu runner passed all gates at implementation commit 338e374. Pytest passed 22/22, Vitest passed 8/8 and Playwright passed 2/2, with no failed or skipped tests. The production build, both linters, Python formatting and both type checks passed. [Verified workflow run](https://github.com/MayankYadav-ds/RetainIQ/actions/runs/45942895895). The subsequent handoff commit changes documentation only, which the workflow excludes.
