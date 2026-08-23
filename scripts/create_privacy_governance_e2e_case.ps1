cd "C:\AI Folder\EasyChatBot-Hackathon"

Write-Host "============================================================"
Write-Host "=== CREATE PRIVACY GOVERNANCE E2E CASE ====================="
Write-Host "============================================================"

$body = @{
    case_id = "CASE-E2E-003"
} | ConvertTo-Json


$response = Invoke-RestMethod `
    "http://127.0.0.1:8000/api/privacy/governance/demo/create-case" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body


Write-Host ""
Write-Host "============================================================"
Write-Host "=== CREATED CASE ==========================================="
Write-Host "============================================================"

$response | ConvertTo-Json -Depth 10


Write-Host ""
Write-Host "============================================================"
Write-Host "=== VALIDATE CASE =========================================="
Write-Host "============================================================"


$case = Invoke-RestMethod `
    "http://127.0.0.1:8000/api/privacy/governance/cases/$($response.case_id)"


$case | ConvertTo-Json -Depth 10