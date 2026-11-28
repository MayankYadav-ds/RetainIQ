# Reproduce Phase 2

Use the Windows dependency installation instructions in the [README](../README.md#run-locally-on-windows). No dependency version changes or new scientific packages were needed. The workflow uses Python 3.11 and its standard library, Pydantic from the existing lock, and the Phase 1 immutable source registry.

```powershell
$v = '461e2bba687bc6e8f52284c9'
$py = '.\backend\.venv\Scripts\python.exe'
& $py -m retainiq.analysis.cli audit-partitions --version $v
& $py -m retainiq.analysis.cli create-folds --version $v
& $py -m retainiq.analysis.cli run --version $v
& $py -m retainiq.analysis.cli profile --version $v
& $py -m retainiq.analysis.cli associations --version $v
& $py -m retainiq.analysis.cli features --version $v --set FS03
& $py -m retainiq.analysis.cli transform --version $v --set FS03
& $py -m retainiq.analysis.cli verify --version $v
python scripts/reconcile_analysis.py --version $v --view 136a09a0f2ec6a66bf3ca6f3
```

Use --root to select a private dataset store and --json for machine-readable output. The registry hashes source inputs, split files, policy, schema, feature specs, seed and Python version. It stages analysis in a separate directory and atomically publishes a verified report, fold memberships, unfitted feature matrices, demonstration fit state, and manifest. Running it twice must match artifact hashes. Analysis paths are ignored by Git under the default root; all custom roots must also remain outside tracked content. Never publish row artifacts.

To view the real UCI aggregate report locally set `$env:RETAINIQ_ANALYTICS_DATASETS = '["uci_iranian_churn"]'` before starting the backend. It must also be in RETAINIQ_PUBLIC_DATASETS, enabled by default for UCI. Absent that opt-in, the analytical API returns an empty result. The workspace provides Analytics, Feature Lab and Evaluation design pages. The API does not serve membership files, state files or row matrices. Public authentication and tenant isolation are outside Phase 2.
