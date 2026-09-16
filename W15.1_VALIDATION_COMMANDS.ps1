# Run from repository root.
Set-Location "C:\AI Folder\EasyChatBot-Hackathon"

# Targeted Developer Admin tests
& ".\.venv\Scripts\python.exe" -m pytest `
  "backend\tests\application\developer_admin" `
  -q

# Infrastructure Developer Admin tests (if present)
& ".\.venv\Scripts\python.exe" -m pytest `
  "backend\tests\infrastructure" `
  -q

# Backend import boundary
Set-Location ".\backend"
& "..\.venv\Scripts\python.exe" -c "import app; print('BACKEND APP:', app.__file__)"
& "..\.venv\Scripts\python.exe" -c "from app.application.academy.academy_activation import AcademyActivationConfig; print('ACADEMY IMPORT: OK')"

Set-Location ".."

# Full backend regression
& ".\.venv\Scripts\python.exe" -m pytest backend\tests -q

# Frontend regression
Set-Location ".\frontend"
npm run build
Set-Location ".."
