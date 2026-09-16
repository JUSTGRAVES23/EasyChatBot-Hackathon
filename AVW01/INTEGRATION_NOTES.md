# AVW-01 Integration Notes

Canonical backend:
`C:\AI Folder\EasyChatBot-Hackathon\backend`

Relevant existing components:
- `app/api/authentication.py`
- `app/application/identity/authentication_service.py`
- `app/application/identity/authentication_email_service.py`
- `app/infrastructure/auth/postgresql_auth_repository.py`
- `cybersecurity/email/email_provider_manager.py`
- `cybersecurity/email/resend_email_provider.py`
- `app/main.py`

`app/application/composition/academy_production.py` composes Academy notifications; do not assume it is the authentication composition root.

`api_authentication_reference.py` should not be changed unless confirmed runtime-authoritative.

The current `app.main.create_application()` composes the authentication repository on application state and includes the authentication router. The implementation should preserve this model or extend it minimally.
