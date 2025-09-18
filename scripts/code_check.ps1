param()

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Change to project root directory
Push-Location $ProjectRoot

try {
    # Try to use activated virtual environment first, fall back to project venv
    $PythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCmd -and $env:VIRTUAL_ENV) {
        $Python = "python"
    } elseif (Test-Path ".\.venv\Scripts\python.exe") {
        $Python = ".\.venv\Scripts\python.exe"
    } else {
        Write-Error "No virtual environment found. Please activate venv or ensure .venv exists in project root."
        exit 1
    }

    & $Python -m ruff check . ; if ($LASTEXITCODE -ne 0) { exit 1 }
    & $Python -m black --check . ; if ($LASTEXITCODE -ne 0) { exit 1 }
    & $Python -m mypy . ; if ($LASTEXITCODE -ne 0) { exit 1 }
    & $Python -m pytest -q ; if ($LASTEXITCODE -ne 0) { exit 1 }
    & $Python -m bandit -q -r . ; if ($LASTEXITCODE -ne 0) { exit 1 }
    & $Python -m pip_audit
} finally {
    # Always return to original directory
    Pop-Location
}
