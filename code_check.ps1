param()
.\.venv\Scripts\python.exe -m ruff check . ; if ($LASTEXITCODE -ne 0) { exit 1 }
.\.venv\Scripts\python.exe -m black --check . ; if ($LASTEXITCODE -ne 0) { exit 1 }
.\.venv\Scripts\python.exe -m mypy . ; if ($LASTEXITCODE -ne 0) { exit 1 }
.\.venv\Scripts\python.exe -m pytest -q ; if ($LASTEXITCODE -ne 0) { exit 1 }
.\.venv\Scripts\python.exe -m bandit -q -r . ; if ($LASTEXITCODE -ne 0) { exit 1 }
.\.venv\Scripts\python.exe -m pip_audit
