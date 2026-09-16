Set-Location "C:\AI Folder\EasyChatBot-Hackathon\backend"

& "..\.venv\Scripts\python.exe" -m uvicorn app.main:create_application --factory --host 127.0.0.1 --port 8000