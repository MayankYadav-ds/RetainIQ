"""Run local quality gates sequentially from the repository root."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
python = root / "backend/.venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
npm = "npm.cmd" if os.name == "nt" else "npm"
commands = [
    ([str(python), "-m", "ruff", "check", "backend"], root),
    ([str(python), "-m", "ruff", "format", "--check", "backend"], root),
    ([str(python), "-m", "mypy", "--config-file", "backend/pyproject.toml", "backend/src"], root),
    ([str(python), "-m", "pytest", "backend/tests", "-q"], root),
    *[([npm, "run", task], root / "frontend") for task in
      ["lint", "typecheck", "test", "build", "e2e"]],
]
for command, cwd in commands:
    print("Running", " ".join(command), flush=True)
    result = subprocess.run(command, cwd=cwd)
    if result.returncode:
        sys.exit(result.returncode)
