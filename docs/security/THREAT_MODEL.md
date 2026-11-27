# Preliminary threat model
The table below records the Phase 0 baseline. For Phase 1 file ingestion, archive constraints, metadata allowlists and local storage risks, see [Data privacy](../DATA_PRIVACY.md) and [Data engineering](../DATA_ENGINEERING.md).

Assets: code, configuration, future customer records, model artifacts and workspace identity.
Adversaries: anonymous remote callers, malicious tenants, compromised dependencies and local users.
Phase 0 has GET metadata only. Local OS access is trusted; public hostile deployment is not validated.

| Threat | Current protection / limitation | Required before future exposure |
|---|---|---|
| Authentication/session theft | No login or sensitive APIs | Secure HttpOnly SameSite cookies, session expiry, fixation protection |
| Authorization/BOLA/cross-workspace access | No tenant records | Server-derived scope on every query/export/artifact; denial tests |
| Malicious uploads | No upload endpoint | Size/type/schema limits, quarantine, no executable parsing, bounded decompression |
| CSV formula injection | No CSV export | Escape =,+,-,@ and control-prefixed cells; preserve source separately |
| SQL injection | Constant SELECT 1 only; SQLAlchemy adapter | Parameterized queries; no user SQL |
| XSS | React text rendering; no raw HTML | CSP, sanitized content, safe download handling |
| CSRF | No cookie auth or mutations; credentials CORS disabled | CSRF tokens/origin checks with cookie-based mutations |
| SSRF | No arbitrary URL fetch | Allowlisted sources, egress controls, reject private/resolved redirect targets |
| Resource exhaustion | Short DB lock/client timeout; no compute APIs | Proxy deadlines/body limits, rate/concurrency quotas, job cancellation |
| Dependencies | Resolved lock files and local audits | Continuous review, provenance, patched releases; lockfile integrity |
| Secrets | Env config, ignored .env, no secret logging | Secret scanning and rotation procedures |
| Sensitive logs | Event/status/duration/request ID only | Audit retention, access controls, redaction regression tests |
| Model tampering | No model loading | Hash verification, trusted formats, signed provenance, no untrusted pickle |
| Retention/deletion | No customer data acquired | TTL policy, deletion of records/artifacts/backups and evidence |
| Host/CORS abuse | Explicit hosts/origins; no wildcard credentials | HTTPS termination, deployment-specific host/origin settings |
| Internal error disclosure | Stable error envelope omits exception details | Keep production debug off; secure operator diagnostics |

Correlation IDs accept only 1–64 ASCII letters, digits, underscore or hyphen, else regenerate.
CORS is a browser control, not authentication. Production config rejects HTTP CORS and default test host.
Residual risks: no public rate limiter, no formal access-control system, no external penetration test,
no PostgreSQL validation, no proven restore SLA. API docs are development-only.
