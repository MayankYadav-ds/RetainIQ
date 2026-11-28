# Phase 3 operator commands and prediction API

From the repository root, install the [locked Windows dependencies](../README.md#run-locally-on-windows). Optional XGBoost/LightGBM support on Windows:

```powershell
backend/.venv/Scripts/python -m pip install --only-binary=:all: -r backend/requirements-boost.lock
```

Use Python 3.11 and Node 24. Base ML dependencies are NumPy 2.2.6, SciPy 1.15.3, scikit-learn 1.7.2 and threadpoolctl 3.8.0, with skops 0.13.0 for safe local serialization. The scientific libraries use permissive BSD-compatible licenses. skops uses BSD-3-Clause. Optional XGBoost 3.0.5 (Apache-2.0) and LightGBM 4.6.0 (MIT) wheels both trained on Windows CPU. The benchmark records exact runtime versions. Ubuntu CI installs the base lock and uses a small genuine nested training run on deterministic synthetic input.

```powershell
$py = '.\backend\.venv\Scripts\python.exe'
$v = '461e2bba687bc6e8f52284c9'
$view = '136a09a0f2ec6a66bf3ca6f3'
& $py -m retainiq.data.cli verify --version $v
& $py -m retainiq.analysis.cli verify --version $v
& $py -m retainiq.ml.cli protocol
& $py -m retainiq.ml.cli benchmark --version $v --view $view
& $py -m retainiq.ml.cli compare --experiment 6dfabb46b6c290694b53914a --detailed
& $py -m retainiq.ml.cli freeze --version $v --view $view --experiment 6dfabb46b6c290694b53914a
& $py -m retainiq.ml.cli inspect --model 2234d0279bb9bd18d77c27b3
& $py -m retainiq.ml.cli verify --model 2234d0279bb9bd18d77c27b3
```

Artifacts are local. Substituting a different dependency set changes the experiment ID. To reconstruct the known eligible view, use the Phase 2 procedure with its pinned inputs and verified Python version. Run the frozen final command only with the prerequisites in the protocol and an explicit local decision to access the holdout. The completed store returns the existing receipt. Reconciliation checks saved evidence without model refitting.

```powershell
& $py -m retainiq.ml.cli evaluate-final --model 2234d0279bb9bd18d77c27b3 --ack-final
python scripts/reconcile_ml.py --experiment 6dfabb46b6c290694b53914a --receipt 6f0e95d28d791f4d703cdac4743432f762805a0374f24569bbb878f33f034b79
```

Start the backend in a separate terminal.

```powershell
$env:RETAINIQ_ACTIVE_MODEL = '2234d0279bb9bd18d77c27b3'
$env:RETAINIQ_ANALYTICS_DATASETS = '["uci_iranian_churn"]'
cd backend
.venv/Scripts/python -m uvicorn retainiq.main:create_app --factory --no-access-log --host 127.0.0.1 --port 8000
```

Run npm --prefix frontend run dev in a separate terminal at the root. Open #models and #predict at http://127.0.0.1:5173. The API docs are at http://127.0.0.1:8000/docs. Demonstration request using invented values:

```powershell
$x = @{call_failure=3; complains=0; subscription_length=17; seconds_of_use=1200; frequency_of_use=24; frequency_of_sms=8; distinct_called_numbers=9; tariff_plan=1}
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/predictions/single -ContentType 'application/json' -Body ($x | ConvertTo-Json)
```

POST /api/v1/predictions/batch wraps inputs in rows. Inputs require all eight strict bounded integer fields. Only complaint codes 0/1 and tariff codes 1/2 are supported. Each request is limited to 64 KiB and batches to 100 rows or RETAINIQ_PREDICTION_BATCH_LIMIT if lower. A single concurrent model call is allowed. Excess waiting can receive 429. Input validation errors are sanitized and requests are neither persisted nor recorded in the application log. Simple observed-range warnings cover marginal ranges only. Response metadata separates raw and calibrated probabilities, threshold, class, tier, model identity, feature version and target.

GET /api/v1/models, /models/active, /models/benchmark and /models/evaluation under the same prefix expose only explicitly activated aggregate evidence. The final threshold is read-only. Local SQLite liveness and readiness do not depend on model activation. Run Chromium installation in frontend with npx playwright install chromium, then python scripts/check.py from the root.
