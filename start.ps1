# Avia - Single-Command Startup Script
# Launches backend (FastAPI) + frontend (React) together.
# Usage:  .\start.ps1

$ErrorActionPreference = "Stop"

# Load API key from .env file (never committed to git)
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), 'Process')
        }
    }
}

if (-not $env:GEMINI_API_KEY) {
    Write-Host ""
    Write-Host "  ERROR: GEMINI_API_KEY not set." -ForegroundColor Red
    Write-Host "  Create a .env file in the project root with:" -ForegroundColor Yellow
    Write-Host "    GEMINI_API_KEY=your_key_here" -ForegroundColor Gray
    Write-Host "  Get a key at: https://aistudio.google.com/apikey" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host "         Avia - Starting Up                    " -ForegroundColor Cyan
Write-Host "     Fraud Investigation Platform              " -ForegroundColor Cyan
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  GenAI:    Gemini 2.0 Flash (google.genai)" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "  Login:    jsmith / avia2026" -ForegroundColor Gray
Write-Host ""

Write-Host "[1/2] Starting backend..." -ForegroundColor Cyan
$backend = Start-Process -PassThru -NoNewWindow -FilePath python -ArgumentList "-m","uvicorn","api.index:app","--host","0.0.0.0","--port","8000","--reload" -WorkingDirectory $PSScriptRoot

Start-Sleep -Seconds 3

Write-Host "[2/2] Starting frontend..." -ForegroundColor Cyan
$frontend = Start-Process -PassThru -NoNewWindow -FilePath cmd -ArgumentList "/c","npm","start" -WorkingDirectory $PSScriptRoot

Write-Host ""
Write-Host "  Both servers running. Press Ctrl+C to stop." -ForegroundColor Green
Write-Host ""

try {
    while (-not $backend.HasExited -and -not $frontend.HasExited) {
        Start-Sleep -Seconds 1
    }
} finally {
    if (-not $backend.HasExited) { Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue }
    if (-not $frontend.HasExited) { Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue }
    Write-Host ""
    Write-Host "  Avia stopped." -ForegroundColor Red
}
