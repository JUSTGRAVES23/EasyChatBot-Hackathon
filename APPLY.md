# Applying M1.4-E.3

Copy only the files under `backend/` into:
C:\AI Folder\EasyChatBot-Hackathon\backend

Do not overwrite unrelated files.

Wire the bootstrap once from the existing application/bootstrap composition after the PostgreSQL Registry is available. Do not invoke it per HTTP request.

Focused test:
    & "..\.venv\Scripts\python.exe" -m pytest -q tests/unit/operations_center/email_workflows/

Expected: existing tests plus the three bootstrap tests pass.

Academy One Week and Privacy Governance Reminder are intentionally not auto-seeded because the supplied inspection does not establish authoritative scheduler cadence and template-registry identifiers. Complete those mappings from their real production composition before making them authoritative Registry records.
