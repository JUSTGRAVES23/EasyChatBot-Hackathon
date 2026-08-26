$ErrorActionPreference = "Stop"

Write-Host "WS-22.3.2.x persistence verification" -ForegroundColor Cyan

python -m pytest `
  ".\backend\tests\announcements\test_ws22_3_2x_persistence_integration.py" `
  -q

if ($LASTEXITCODE -ne 0) {
    throw "Focused WS-22.3.2.x tests failed."
}

Write-Host "Checking Alembic heads..." -ForegroundColor Cyan
alembic heads

Write-Host ""
Write-Host "IMPORTANT: apply the migration only after reviewing the generated revision:" -ForegroundColor Yellow
Write-Host "  alembic upgrade head"
Write-Host ""
Write-Host "WS-22.3.2.x focused verification passed." -ForegroundColor Green
