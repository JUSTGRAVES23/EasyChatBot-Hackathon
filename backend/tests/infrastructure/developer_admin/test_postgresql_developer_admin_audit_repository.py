import inspect

from app.infrastructure.developer_admin.postgresql_developer_admin_audit_repository import (
    PostgreSQLDeveloperAdminAuditRepository,
)


def test_repository_is_async_and_uses_required_table():
    record_source = inspect.getsource(
        PostgreSQLDeveloperAdminAuditRepository.record
    )
    insert_source = inspect.getsource(
        PostgreSQLDeveloperAdminAuditRepository._insert
    )

    assert "async def record" in record_source
    assert "async def _insert" in insert_source
    assert "developer_admin_audit_events" in insert_source
    assert "INSERT INTO" in insert_source


def test_repository_standalone_record_owns_transaction():
    source = inspect.getsource(PostgreSQLDeveloperAdminAuditRepository.record)

    assert "async with self._session_factory()" in source
    assert "async with session.begin()" in source


def test_repository_supports_transaction_aware_recording():
    source = inspect.getsource(
        PostgreSQLDeveloperAdminAuditRepository.record_in_session
    )

    assert "async def record_in_session" in source
    assert "await self._insert(session, event)" in source
