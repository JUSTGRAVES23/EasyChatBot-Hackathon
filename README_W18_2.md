# W18.2 — Beta World Access Policy

## Objective

Provision one canonical learner with durable `LearnerWorldAccess` for **every World in the authoritative `learning_worlds` catalogue**.

There is deliberately no hard-coded list such as French/Polish/Spanish.

## Architectural decision

`enabled` is treated as **runtime availability**, not as the definition of the learner's World portfolio.

Therefore:

- enabled Worlds receive access;
- disabled Worlds also receive durable Beta access;
- disabled Worlds must still be rejected by runtime/Study Mode entry until enabled;
- the catalogue remains the only source of World scope.

This is an explicit W18.2 provisioning-policy extension. Existing ordinary WorldAccessService callers continue to reject disabled Worlds unless they deliberately opt into the provisioning flag.

## Files

Replace:

- `backend/app/application/services/world_access_service.py`
- `backend/app/application/world_catalogue/repositories.py`
- `backend/app/application/world_catalogue/service.py`
- `backend/app/infrastructure/persistence/postgresql_learning_world_catalogue_repository.py`
- `backend/tests/application/world_catalogue/test_learning_world_catalogue_service.py`

Add:

- `backend/app/application/services/beta_world_access_service.py`
- `backend/tests/application/services/test_beta_world_access_service.py`

No Alembic migration is required for W18.2 because W18.1 already created the durable access table.

## Integration boundary

`BetaWorldAccessService` is the Beta policy layer.

It depends on:

1. the read-only Beta-user boundary;
2. the canonical identity reader;
3. the authoritative World catalogue;
4. the generic World Access authorization service.

It does not:
- own Telegram;
- modify `active_world_id`;
- create announcements;
- create Study Mode sessions;
- use `CommunityMembership`;
- contain a language/World allow-list.

Registration/Telegram provisioning should call this service in the later W18.6 orchestration layer.

## Required validation

From:

`C:\AI Folder\EasyChatBot-Hackathon\backend`

Run targeted tests first:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  .\tests\application\services\test_world_access_service.py `
  .\tests\application\services\test_beta_world_access_service.py `
  .\tests\application\world_catalogue\test_learning_world_catalogue_service.py `
  -q
```

Then the W18 regression set:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  .\tests\domain\test_learner_world_access.py `
  .\tests\application\services\test_world_access_service.py `
  .\tests\application\services\test_beta_world_access_service.py `
  .\tests\application\world_catalogue\test_learning_world_catalogue_service.py `
  -q
```

Then formatting/lint/type checks using the repository's existing scripts.

Do **not** run an Alembic migration for this workstream.

## Important

This package was prepared from the W18.2 canonical inspection supplied in the conversation. The local Windows repository was not executable from this environment, so the package is **not claimed as locally tested**. Apply it to the canonical checkout and run the commands above before sign-off.
