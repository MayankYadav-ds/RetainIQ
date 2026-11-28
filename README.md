# RetainIQ

RetainIQ is a local-first customer retention intelligence platform. Version 0.4.0 adds a protected churn benchmark, calibrated local inference, Model Lab and Prediction simulator. The landing page shows which capabilities are available and which are planned. The repository contains source code and aggregate evidence. Trained model artifacts and customer records stay in the local data store.

## Run locally on Windows

Use Python 3.11 and Node 24. From the repository root, install once in PowerShell. The SQLAlchemy setting selects its supported pure-Python build on this Windows host.

```powershell
python -m venv backend/.venv
$env:DISABLE_SQLALCHEMY_CEXT = '1'
backend/.venv/Scripts/python -m pip install --no-binary=SQLAlchemy -r backend/requirements.lock
Remove-Item Env:DISABLE_SQLALCHEMY_CEXT
backend/.venv/Scripts/python -m pip install --no-deps -e backend
npm --prefix frontend ci
```

Start the API in the first terminal from the repository root.

```powershell
cd backend
.venv/Scripts/python -m uvicorn retainiq.main:create_app --factory --no-access-log --host 127.0.0.1 --port 8000
```

Start the UI in a second terminal from the repository root.

```powershell
npm --prefix frontend run dev
```

Open [the local UI](http://127.0.0.1:5173), [API metadata](http://127.0.0.1:8000) or [interactive API docs](http://127.0.0.1:8000/docs). The UI checks version and readiness. Stop either service with Ctrl+C. The default database is created in the backend working directory. To customize settings, copy .env.example to backend/.env and run the API from backend. VITE_API_BASE_URL belongs in frontend/.env.local and is public at build time.

## Verify

Stop development servers first so the smoke suite can own ports 8000 and 4173 with its test CORS setting. Install Chromium once and run all gates.

```powershell
cd frontend
npx playwright install chromium
cd ..
python scripts/check.py
```

On Linux use backend/.venv/bin/python in place of the Windows executable, install the lock with pip, use npm ci, and install Chromium with npx playwright install --with-deps chromium. See the workflow for the exact CI sequence. Optional local containers use docker compose up --build (UI port 8080) and docker compose down to stop. Container runtime status is recorded in the handoff.

## API

| GET route | Meaning |
|---|---|
| / | Product, phase and version |
| /health | Process can answer, independent of storage |
| /ready | A real database query succeeded, otherwise 503 |
| /api/v1/version | Version contract consumed by the UI |

Errors include a safe message, code and request ID. Use X-Request-ID to correlate with structured application logs. Production configuration requires explicit hosts and HTTPS browser origins.

## Engineering and science

Start with the [project handoff](docs/PROJECT_STATE.md), [product requirements](docs/PRODUCT_REQUIREMENTS.md), [architecture](docs/architecture/OVERVIEW.md), [decisions](docs/adr), [threat model](docs/security/THREAT_MODEL.md), [ML integrity contract](docs/ML_INTEGRITY_CONTRACT.md), [dataset strategy](docs/DATASET_STRATEGY.md) and [deployment strategy](docs/DEPLOYMENT_STRATEGY.md).

Run the full local workflow with `backend/.venv/Scripts/retainiq-data run --dataset uci_iranian_churn` from the root, then open [Data Explorer](http://127.0.0.1:5173/#datasets). See the [operator guide](docs/DATA_ENGINEERING.md), [verified report](docs/DATA_QUALITY_REPORT.md), [dictionary](docs/DATA_DICTIONARY.md) and [split protocol](docs/EVALUATION_PROTOCOL.md). Evidence of intervention effectiveness requires a separate causal evaluation.

## Development analytics

Run the [Phase 2 workflow](docs/FEATURE_ENGINEERING.md) after UCI ingestion. It verifies the original partition checksums, excludes shared approved-feature vectors from development and generates the local aggregate report. To enable the UCI report in the local API, set RETAINIQ_ANALYTICS_DATASETS to the JSON list of approved dataset IDs before backend startup. Open Analytics, Feature Lab or Evaluation design from the navigation.

## Machine learning and local inference

See the [operator commands](docs/PREDICTION_API.md), [benchmark](docs/MODEL_BENCHMARK.md), [final holdout evidence](docs/FINAL_EVALUATION.md) and [model card](docs/MODEL_CARD.md).
