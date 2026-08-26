# Copy map

## Backend

Copy these files into the corresponding existing WS-22 backend locations:

- backend/app/domain/announcements/template_models.py
- backend/app/application/announcements/repositories.py
- backend/app/application/announcements/template_registry.py
- backend/app/infrastructure/announcements/in_memory_repositories.py
- backend/app/application/announcements/template_editor_models.py
- backend/app/application/announcements/template_editor_service.py
- backend/app/interfaces/announcements/template_editor_router.py
- backend/tests/announcements/test_ws22_2x_template_editor_integration.py

The first four are additive WS-22.1-compatible replacements. Review the
production repository implementation before changing it; the in-memory
adapter is only for tests.

## Frontend

Copy:

- frontend/app/lib/api/announcementTemplateEditor.ts
- frontend/app/components/operations-center/announcement-operations/TemplateDrivenPublicationEditor.tsx

Replace the existing create-page import with the supplied:

- frontend/app/operations-center/announcement-operations/create/page.ws22-2x.tsx

Do not overwrite the existing create page until the new editor has been
reviewed.

## Router composition

Add the returned router from:

    create_template_editor_router(editor_service)

to the existing FastAPI application/router composition.

Do not instantiate repositories or services inside the HTTP router.

## Tests

Backend:

    python -m pytest backend/tests/announcements/test_ws22_2x_template_editor_integration.py -q

Frontend:

    npx playwright test tests/ws22_2x_template_editor.spec.ts

Then run the existing WS-22.1 and WS-22.2 regression suites.
