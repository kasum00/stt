param(
    [switch]$SkipFrontend,
    [switch]$SkipBackend
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $repoRoot 'ai'
$webRoot = Join-Path $repoRoot 'herstyleai-client\apps\web'
$pythonPath = Join-Path $backendRoot '.venv\Scripts\python.exe'

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $Command $($Arguments -join ' ')"
    }
}

Set-Location $repoRoot

if (-not $SkipBackend) {
    $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pythonLauncher) {
        throw 'Python launcher (py) was not found. Install Python 3.10+ and enable it in PATH.'
    }

    if (-not (Test-Path $pythonPath)) {
        Write-Host 'Creating ai\.venv ...' -ForegroundColor Cyan
        Invoke-Checked -Command $pythonLauncher.Source -Arguments @('-3', '-m', 'venv', (Join-Path $backendRoot '.venv'))
    }

    Write-Host 'Installing backend dependencies ...' -ForegroundColor Cyan
    Invoke-Checked -Command $pythonPath -Arguments @('-m', 'pip', 'install', '--upgrade', 'pip')
    Invoke-Checked -Command $pythonPath -Arguments @('-m', 'pip', 'install', '-r', (Join-Path $backendRoot 'requirements-backend.txt'))
    Invoke-Checked -Command $pythonPath -Arguments @('-m', 'pip', 'install', 'torch', 'torchvision', '--index-url', 'https://download.pytorch.org/whl/cpu')
    Invoke-Checked -Command $pythonPath -Arguments @('-m', 'pip', 'install', '-r', (Join-Path $backendRoot 'requirements-ai.txt'))

    $backendEnv = Join-Path $backendRoot '.env'
    if (-not (Test-Path $backendEnv)) {
        Copy-Item (Join-Path $backendRoot '.env.example') $backendEnv
        Write-Host 'Created ai\.env from ai\.env.example. Edit DATABASE_URL and JWT_SECRET_KEY before starting the API.' -ForegroundColor Yellow
    }
}

if (-not $SkipFrontend) {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npm) {
        throw 'npm was not found. Install Node.js 20+ and enable it in PATH.'
    }

    $frontendEnv = Join-Path $webRoot '.env.local'
    if (-not (Test-Path $frontendEnv)) {
        Copy-Item (Join-Path $webRoot '.env.example') $frontendEnv
        Write-Host 'Created apps/web/.env.local from .env.example.' -ForegroundColor Green
    }

    if (-not (Test-Path (Join-Path $webRoot 'node_modules'))) {
        Write-Host 'Installing frontend dependencies ...' -ForegroundColor Cyan
        Push-Location $webRoot
        try {
            Invoke-Checked -Command $npm.Source -Arguments @('install')
        }
        finally {
            Pop-Location
        }
    }
}

Write-Host ''
Write-Host 'Setup complete.' -ForegroundColor Green
Write-Host '1. Start PostgreSQL and create the herstyleai database.'
Write-Host '2. Edit ai\.env and replace the database URL and JWT secret.'
Write-Host '3. Run .\scripts\start-backend.ps1 in one terminal.'
Write-Host '4. Run .\scripts\start-web.ps1 in another terminal.'
