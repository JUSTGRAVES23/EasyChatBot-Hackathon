cd "C:\AI Folder\EasyChatBot-Hackathon"

python -m pytest `
  ".\backend\tests\announcements\test_ws22_3_2_durable_execution.py" `
  -q

python -m pytest `
  ".\backend\tests\announcements" `
  -q
