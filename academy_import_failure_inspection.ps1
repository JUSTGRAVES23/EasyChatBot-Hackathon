Write-Output "============================================================"
Write-Output "EASYCHATBOT ACADEMY IMPORT FAILURE - FULL INSPECTION"
Write-Output "============================================================"
Write-Output ""

Write-Output "===== 1. ACADEMY DIRECTORIES ====="
Get-ChildItem ".\backend\app" -Recurse -Directory |
    Where-Object {
        $_.FullName -match "academy"
    } |
    Select-Object FullName

Write-Output ""
Write-Output "===== 2. ALL ACADEMY FILES ====="
Get-ChildItem ".\backend\app" -Recurse -File |
    Where-Object {
        $_.FullName -match "academy"
    } |
    Select-Object FullName, Length

Write-Output ""
Write-Output "===== 3. MAIN.PY ACADEMY IMPORTS ====="
Get-Content ".\backend\app\main.py" |
    Select-String -Pattern "academy|Academy"

Write-Output ""
Write-Output "===== 4. ALL PYTHON REFERENCES TO ACADEMY ACTIVATION ====="
Get-ChildItem ".\backend" -Recurse -File -Filter "*.py" |
    Select-String -Pattern "academy_activation|AcademyActivationConfig|academy_activation" |
    Select-Object Path, LineNumber, Line

Write-Output ""
Write-Output "===== 5. ALL PYTHON REFERENCES TO ACADEMY ====="
Get-ChildItem ".\backend" -Recurse -File -Filter "*.py" |
    Select-String -Pattern "academy" |
    Select-Object Path, LineNumber, Line

Write-Output ""
Write-Output "===== 6. GIT ACADEMY FILES ====="
git ls-files |
    Select-String -Pattern "academy"

Write-Output ""
Write-Output "===== 7. GIT STATUS ====="
git status --short

Write-Output ""
Write-Output "===== 8. ACADEMY PYPROJECT / PACKAGE REFERENCES ====="
Get-ChildItem "." -Recurse -File |
    Where-Object {
        $_.Name -in @(
            "pyproject.toml",
            "requirements.txt",
            "requirements-dev.txt",
            "setup.py",
            "setup.cfg"
        )
    } |
    ForEach-Object {
        Write-Output ""
        Write-Output "### $($_.FullName)"
        Select-String -Path $_.FullName -Pattern "academy" -ErrorAction SilentlyContinue
    }

Write-Output ""
Write-Output "===== 9. EXACT IMPORT TEST ====="
& ".\.venv\Scripts\python.exe" -c "from app.application.academy.academy_activation import AcademyActivationConfig; print('ACADEMY IMPORT: PASS')" 2>&1

Write-Output ""
Write-Output "===== 10. APPLICATION PACKAGE TREE ====="
Get-ChildItem ".\backend\app\application" -Recurse -File |
    Select-Object FullName

Write-Output ""
Write-Output "============================================================"
Write-Output "END INSPECTION"
Write-Output "============================================================"
