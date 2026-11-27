# Recruiter deployment strategy

Reviewed 2026-11-27. No public application has been deployed. Native Windows execution is the reference. Installation needs internet access for public dependencies. Local application traffic needs no external service. The development Swagger UI uses CDN assets, with the raw OpenAPI contract also available locally.

| Candidate | Fit and resource envelope | Failure and cost boundary |
|---|---|---|
| GitHub Pages, public GitHub Free repository | Public documentation or a noncommercial portfolio frontend. Static assets only, with browser-side CPU and memory. Published site up to 1 GB, soft 100 GB/month bandwidth. | No application server, writable database or server cold start. Rebuild with the correct repository base path. Avoid sensitive transactions and commercial SaaS use. Existing GitHub account, no paid plan needed for public Pages. [GitHub limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) |
| Cloudflare Pages Free | Alternative static UI. One concurrent build, 500 builds/month, 20-minute build timeout, 20,000 files and 25 MiB/asset. No server CPU/RAM allocation for static requests. | Requires a provider account. Keep Functions, paid storage and metered add-ons disabled. Static files cannot store private workspaces. Card-free signup has not been verified for this account. [Pages limits](https://developers.cloudflare.com/pages/platform/limits/) |
| Render Free web service | Disposable FastAPI demo. 0.1 CPU, 512 MB RAM, 750 shared free instance-hours/month. Build and transfer allowances also apply. Precompute expensive inference. | Sleeps after 15 idle minutes. Startup can take about one minute, longer than the UI timeout. Files including local SQLite disappear on restart/redeploy/sleep. Free Postgres expires after 30 days. Requires an account. Proceed only if a workspace with no payment method suspends service on exhaustion. Decline any card verification or automatic overage billing. [Free service terms](https://render.com/docs/free) and [compute limits](https://render.com/docs/compute-plans) |

## Release path

1. Prove the sample license permits redistribution or use clearly labeled synthetic records. Publish data provenance, a reproducible evaluation report and model limitations.
2. Give each visitor a server-issued expiring workspace without registration. Derive authorization from the session on every read, write and export. Verify cross-workspace denials, expiry, quotas, cleanup and a reset action.
3. Show reproducible per-customer explanations and interactive cost/budget simulations. Precompute model outputs where CPU or memory is limited. Display assumptions alongside results and carry them into exports.
4. Build the UI for the real HTTPS API origin. Configure exact CORS origins, trusted hosts, HTTPS, request/body limits, secure cookies and a warm-up/retry state. Check production logs and repeated cold starts. Test expiry and restarts on disposable records.
5. Recheck account-specific billing, storage, bandwidth and hard suspension terms before provisioning. If access requires payment information or risks automatic charges, retain the native demo. A static-only fallback can later run functional read-only explanations and simulations on approved bundled samples. Retain local execution for authenticated workflows. Do not publish partially functioning guest workflows.

CI uses a standard public Ubuntu runner with read-only repository permission and no artifact or cache uploads. Paid larger runners and private-repository jobs are excluded. [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
