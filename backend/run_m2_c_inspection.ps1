$ErrorActionPreference = "Continue"

$Out = Join-Path (Get-Location) "M2_C_IMPLEMENTATION_INSPECTION_REAL.txt"

function Section($Title) {
    Add-Content $Out ""
    Add-Content $Out ("=" * 80)
    Add-Content $Out $Title
    Add-Content $Out ("=" * 80)
}

Remove-Item $Out -Force -ErrorAction SilentlyContinue

Add-Content $Out "EASYCHATBOT — M2-C POLISH PRIVATE CHAT"
Add-Content $Out "REAL READ-ONLY IMPLEMENTATION INSPECTION"
Add-Content $Out ("Generated: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
Add-Content $Out ("Repository root: " + (Get-Location))
Add-Content $Out ""

Section "1. GIT STATE"
git status --short 2>&1 | Out-File $Out -Append
Add-Content $Out "`n--- BRANCH ---"
git branch --show-current 2>&1 | Out-File $Out -Append
Add-Content $Out "`n--- DIFF STAT ---"
git diff --stat 2>&1 | Out-File $Out -Append

Section "2. DIRECTORY TREE"
Get-ChildItem -Recurse -File |
    Where-Object {
        $_.FullName -notmatch '\\.git\\' -and
        $_.FullName -notmatch '\\__pycache__\\' -and
        $_.FullName -notmatch '\\.pytest_cache\\'
    } |
    ForEach-Object {
        $_.FullName.Substring((Get-Location).Path.Length + 1)
    } |
    Sort-Object |
    Out-File $Out -Append

Section "3. AUTHENTICATION / IDENTITY / AUTHORIZATION"

foreach ($f in @(
    ".\app\api\authentication.py",
    ".\app\api\dependencies\identity.py",
    ".\app\application\authorization\authorization_service.py"
)) {
    if (Test-Path $f) {
        Add-Content $Out "`n===== $f ====="
        Get-Content $f | Out-File $Out -Append
    }
}

Section "4. WORLD CATALOGUE / RESOLUTION"

Get-ChildItem .\app -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match "world.*catalog|catalog.*world|world_resolver|world_context" -and
        $_.FullName -notmatch '\\__pycache__\\'
    } |
    Sort-Object FullName |
    ForEach-Object {
        Add-Content $Out "`n===== $($_.FullName) ====="
        Get-Content $_.FullName | Out-File $Out -Append
    }

Section "5. WORLD CONFIGURATION"

if (Test-Path ".\app\configuration\worlds") {
    Get-ChildItem .\app\configuration\worlds -File |
        Sort-Object Name |
        ForEach-Object {
            Add-Content $Out "`n===== $($_.FullName) ====="
            Get-Content $_.FullName | Out-File $Out -Append
        }
}

Section "6. CONVERSATION / RUNTIME"

Get-ChildItem .\app -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -match "conversation|runtime" -and
        $_.Extension -eq ".py" -and
        $_.FullName -notmatch '\\__pycache__\\'
    } |
    Sort-Object FullName |
    ForEach-Object {
        Add-Content $Out "`n===== $($_.FullName) ====="
        Get-Content $_.FullName | Out-File $Out -Append
    }

Section "7. PROVIDER BOUNDARY"

Get-ChildItem .\app -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -match "provider" -and
        $_.Extension -eq ".py" -and
        $_.FullName -notmatch '\\__pycache__\\'
    } |
    Sort-Object FullName |
    ForEach-Object {
        Add-Content $Out "`n===== $($_.FullName) ====="
        Get-Content $_.FullName | Out-File $Out -Append
    }

Section "8. TELEGRAM ISOLATION"

Get-ChildItem .\app -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Extension -eq ".py" -and
        $_.FullName -notmatch '\\__pycache__\\'
    } |
    Select-String -Pattern `
        "TelegramConversationService",
        "telegram_user_hash",
        "handle_telegram_message",
        "ConversationEvent" |
    ForEach-Object {
        "$($_.Path):$($_.LineNumber):$($_.Line.Trim())"
    } |
    Out-File $Out -Append

Section "9. DATABASE / PERSISTENCE"

Get-ChildItem .\app -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -match "model|persistence|repository" -and
        $_.Extension -eq ".py" -and
        $_.FullName -notmatch '\\__pycache__\\'
    } |
    Sort-Object FullName |
    ForEach-Object {
        Add-Content $Out "`n===== $($_.FullName) ====="
        Get-Content $_.FullName | Out-File $Out -Append
    }

Section "10. ALEMBIC"

if (Test-Path ".\alembic") {
    Get-ChildItem .\alembic -Recurse -File |
        Where-Object {
            $_.Extension -eq ".py"
        } |
        Sort-Object FullName |
        ForEach-Object {
            Add-Content $Out "`n===== $($_.FullName) ====="
            Get-Content $_.FullName | Out-File $Out -Append
        }
}

Section "11. APPLICATION COMPOSITION"

if (Test-Path ".\app\main.py") {
    Add-Content $Out "`n===== .\app\main.py ====="
    Get-Content .\app\main.py | Out-File $Out -Append
}

Section "12. API ROUTERS"

Get-ChildItem .\app\api -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Extension -eq ".py" -and
        $_.FullName -notmatch '\\__pycache__\\'
    } |
    Sort-Object FullName |
    ForEach-Object {
        Add-Content $Out "`n===== $($_.FullName) ====="
        Get-Content $_.FullName | Out-File $Out -Append
    }

Section "13. RELEVANT TEST FILES"

Get-ChildItem .\tests -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Extension -eq ".py" -and
        $_.FullName -notmatch '\\__pycache__\\'
    } |
    Sort-Object FullName |
    ForEach-Object {
        Add-Content $Out "`n===== $($_.FullName) ====="
        Get-Content $_.FullName | Out-File $Out -Append
    }

Section "14. DEPENDENCIES"

foreach ($f in @(
    ".\pyproject.toml",
    ".\requirements.txt",
    ".\requirements-dev.txt"
)) {
    if (Test-Path $f) {
        Add-Content $Out "`n===== $f ====="
        Get-Content $f | Out-File $Out -Append
    }
}

Section "15. EXISTING CHAT ROUTES / SECURITY REFERENCES"

Get-ChildItem .\app -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Extension -eq ".py" -and
        $_.FullName -notmatch '\\__pycache__\\'
    } |
    Select-String -Pattern `
        "private-chat",
        "private_chat",
        "/worlds/",
        "easychatbot_session",
        "get_current_principal",
        "require_authenticated",
        "require_permission",
        "conversation_id",
        "user_id" |
    ForEach-Object {
        "$($_.Path):$($_.LineNumber):$($_.Line.Trim())"
    } |
    Out-File $Out -Append

Section "16. PYTEST COLLECTION"

python -m pytest --collect-only -q 2>&1 | Out-File $Out -Append

Section "17. TARGETED BASELINE"

python -m pytest -q tests -k "world or authentication or conversation or telegram or catalogue" --maxfail=20 2>&1 |
    Out-File $Out -Append

Section "18. FULL REGRESSION BASELINE"

python -m pytest -q --maxfail=20 2>&1 |
    Out-File $Out -Append

Section "19. FINAL GIT STATE"

git status --short 2>&1 | Out-File $Out -Append

Add-Content $Out "`nEND OF REAL M2-C INSPECTION"

Write-Host ""
Write-Host "=============================================="
Write-Host "M2-C inspection completed"
Write-Host "=============================================="
Write-Host ""
Write-Host "Output:"
Write-Host (Resolve-Path $Out)
Write-Host ""
Start-Process notepad.exe (Resolve-Path $Out)
