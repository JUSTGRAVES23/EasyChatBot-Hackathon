cd "C:\AI Folder\EasyChatBot-Hackathon"

python -m pytest `
  ".\backend\tests\announcements\test_ws22_3_1_publication_execution_contract.py" `
  -q

python -m pytest `
  ".\backend\tests\announcements" `
  -q
