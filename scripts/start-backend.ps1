$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $repoRoot 'ai'
$pythonPath = Join-Path $backendRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $pythonPath)) {
    throw 'Backend environment is missing. Run .\scripts\setup.ps1 first.'
}

$backendEnv = Join-Path $backendRoot '.env'
if (-not (Test-Path $backendEnv)) {
    throw 'ai\.env is missing. Run .\scripts\setup.ps1, then configure DATABASE_URL and JWT_SECRET_KEY.'
}

$envText = Get-Content $backendEnv -Raw
if ($envText -match 'JWT_SECRET_KEY\s*=\s*change-me') {
    throw 'JWT_SECRET_KEY still has the example value. Set a random secret in ai\.env before starting the API.'
}

Set-Location $backendRoot
$env:PYTHONPATH = Join-Path $backendRoot 'src'

Write-Host 'Applying database migrations ...' -ForegroundColor Cyan
& $pythonPath -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    throw 'Database migration failed. Check PostgreSQL and DATABASE_URL in ai\.env.'
}

Write-Host 'Starting HerStyle AI API at http://127.0.0.1:8000 ...' -ForegroundColor Green
& $pythonPath -m uvicorn herstyle_ai.api.app:app --host 127.0.0.1 --port 8000 --reload
