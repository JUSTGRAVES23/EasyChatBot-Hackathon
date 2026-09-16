from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def test_unit_of_work_owns_one_transaction_and_advisory_lock():
    source = (
        ROOT
        / "backend/app/infrastructure/developer_admin/postgresql_developer_admin_uow.py"
    ).read_text(encoding="utf-8")

    assert "await self._session.begin()" in source
    assert "pg_advisory_xact_lock" in source
    assert "await self._transaction.commit()" in source
    assert "await self._transaction.rollback()" in source


def test_audit_repository_has_transaction_aware_non_committing_entrypoint():
    source = (
        ROOT
        / "backend/app/infrastructure/developer_admin/"
        "postgresql_developer_admin_audit_repository.py"
    ).read_text(encoding="utf-8")

    assert "record_in_session" in source
    assert "async def record(" in source
    assert "async with session.begin()" in source
