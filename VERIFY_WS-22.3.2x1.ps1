$ErrorActionPreference = "Stop"

cd "C:\AI Folder\EasyChatBot-Hackathon"

if (-not $env:DATABASE_URL) {
    throw "DATABASE_URL is not set. Configure the existing PostgreSQL connection before running this integration verification."
}

Write-Host "WS-22.3.2.x.1 — PostgreSQL restart/idempotency verification" -ForegroundColor Cyan

python -m pytest `
  ".\backend\tests\announcements\test_ws22_3_2x1_postgresql_restart_idempotency.py" `
  -q

if ($LASTEXITCODE -ne 0) {
    throw "WS-22.3.2.x.1 PostgreSQL integration verification failed."
}

Write-Host ""
Write-Host "Running announcement regression suite..." -ForegroundColor Cyan

python -m pytest ".\backend\tests\announcements" -q

if ($LASTEXITCODE -ne 0) {
    throw "Announcement regression suite failed."
}

Write-Host ""
Write-Host "WS-22.3.2.x.1 verification PASSED." -ForegroundColor Green
