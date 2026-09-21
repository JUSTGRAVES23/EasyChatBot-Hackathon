Set-Location "C:\AI Folder\EasyChatBot-Hackathon\backend"

Write-Host "=== W19.2 schema verification (read-only) ==="
python ".\scripts\verify_w19_2_schema.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "=== W19.2 targeted application tests ==="
python -m pytest ".\tests\application\world_telegram\test_membership_service.py" -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "=== W19.2 repository contract tests ==="
python -m pytest ".\tests\infrastructure\persistence\test_world_telegram_membership_repository.py" -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "=== W19.1 regression tests ==="
python -m pytest ".\tests\application\world_telegram\test_service.py" -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m pytest ".\tests\infrastructure\persistence\test_world_telegram_destination_repository.py" -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "W19.2 verification sequence completed successfully."
