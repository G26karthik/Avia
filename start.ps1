# Avia - Single-Command Startup Script
# Launches backend (FastAPI) + frontend (React) together.
# Usage:  .\start.ps1

$ErrorActionPreference = "Stop"

$env:GEMINI_API_KEY = "AIzaSyDagJfdsmkQULysVOYncbh49__uaGSwo04"

Write-Host ""
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host "         Avia - Starting Up                    " -ForegroundColor Cyan
Write-Host "     Fraud Investigation Platform              " -ForegroundColor Cyan
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  GenAI:    Gemini 2.5 Flash (google.genai)" -ForegroundColor Green
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
