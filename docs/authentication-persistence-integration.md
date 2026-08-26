# EasyChatBot Authentication Persistence Integration

## Verified source state

The inspected application already contains:

- `AuthenticationService`
- `SessionIdentityProvider`
- `AuthorizationService`
- server-side `easychatbot_session` cookie handling
- PostgreSQL `users`, `user_credentials`, and `user_sessions`

The inspected database, however, did not contain `users.email_verified`, an
email-verification token table, or a persisted role table. The existing
`AuthenticationService` already calls `create_email_verification()` and the
`SessionIdentityProvider` already calls `get_user_roles()`. Those contracts
therefore could not be satisfied safely from the inspected schema alone.

## Implemented persistence slice

`PostgreSQLAuthenticationRepository` provides:

- email/username uniqueness checks
- user creation
- password credential persistence
- hashed email-verification token persistence
- one-time email verification
- user lookup
- password credential lookup
- server-side session creation
- session retrieval/revocation
- identity lookup
- persisted RBAC role lookup

The adapter uses SQLAlchemy Core statements and the existing database session
boundary. It does not create a second user system or introduce JWTs.

## Required migration

`20260826_auth_persistence_integration` must run after the inspected current
Alembic head `20260822_privacy_event_governance`.

It adds:

1. `users.email_verified`
2. `auth_user_roles`
3. `auth_email_verification_tokens`

It does **not** recreate or replace `users`, `user_credentials`, or
`user_sessions`.

## Important integration step

The repository must be composed into `app.state.auth_repository` using the
existing `create_async_database_engine()` and
`create_async_session_factory()` functions from
`backend.app.infrastructure.persistence.database`.

Example composition:

```python
engine = create_async_database_engine()
session_factory = create_async_session_factory(engine)
app.state.auth_repository = PostgreSQLAuthenticationRepository(session_factory)
```

The exact FastAPI lifespan/composition location must be inserted into the
existing application bootstrap rather than creating a second application
composition root.

## RBAC bootstrap

Ordinary registered users should receive `beta_user` only. `operator` and
`admin` roles must be assigned through an explicit controlled administrative
workflow or controlled seed/bootstrap procedure. Do not infer operator status
from email address or username.

## Verification status

The patch is structurally reviewed, but it has **not** been honestly marked as
PostgreSQL-verified because the uploaded artifacts do not expose a live
`DATABASE_URL` connection to this execution environment. Before merge, run:

```powershell
python -m alembic current
python -m alembic heads
python -m alembic upgrade head
pytest -q backend/tests/security
```

Then perform an API smoke test:

1. register
2. verify email
3. login
4. resolve `/auth/me` through `SessionIdentityProvider`
5. verify a `beta_user` cannot publish announcements
6. verify an explicitly seeded `operator` can pass `announcement.publish`
7. logout
8. verify the revoked session no longer resolves
