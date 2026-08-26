# WS-22.0.x verification

cd "C:\AI Folder\EasyChatBot-Hackathon"

python -m pytest `
  ".\backend\tests\announcements\test_ws22_0x_publication_lifecycle_alignment.py" `
  -q

python -m pytest `
  ".\backend\tests\announcements" `
  -q
