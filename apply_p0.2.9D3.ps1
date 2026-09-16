$ErrorActionPreference = "Stop"
Set-Location "C:\AI Folder\EasyChatBot-Hackathon"

$patch = ".\P0.2.9D3_secure_governance_and_api_actor.patch"
if (-not (Test-Path $patch)) { throw "Patch not found: $patch" }

Write-Host "Repository:"
git rev-parse --show-toplevel

Write-Host ""
Write-Host "Working tree BEFORE:"
git status --short

Write-Host ""
Write-Host "Applying patch..."
git apply --check $patch
git apply $patch

Write-Host ""
Write-Host "Working tree AFTER:"
git status --short

Write-Host ""
Write-Host "Next: run the targeted tests from README.md"
