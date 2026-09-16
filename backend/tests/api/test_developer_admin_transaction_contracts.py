from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.api.routes.developer_admin_transaction_contracts import (
    DeveloperAdminCreateTransactionRequest,
    DeveloperAdminExecuteTransactionRequest,
    DeveloperAdminPendingTransactionResponse,
)


def test_create_transaction_request_requires_uuid() -> None:
    request = DeveloperAdminCreateTransactionRequest(
        target_user_id=UUID("11111111-1111-4111-8111-111111111111")
    )
    assert request.target_user_id == UUID("11111111-1111-4111-8111-111111111111")


def test_create_transaction_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        DeveloperAdminCreateTransactionRequest(
            target_user_id=UUID("11111111-1111-4111-8111-111111111111"),
            assurance_level="A2",
        )


def test_execute_request_contains_only_authorization_reference() -> None:
    request = DeveloperAdminExecuteTransactionRequest(
        authorization_id="authorization-001"
    )
    assert request.authorization_id == "authorization-001"


def test_pending_response_is_safe_contract() -> None:
    response = DeveloperAdminPendingTransactionResponse(
        authorization_id="authorization-001",
        transaction_id="transaction-001",
        operation="developer_admin.grant",
        audience="easychatbot.developer_admin",
        target_user_id=UUID("11111111-1111-4111-8111-111111111111"),
        state="pending_user_approval",
        expires_at=datetime(2026, 9, 16, 8, 5, tzinfo=timezone.utc),
    )
    assert response.state == "pending_user_approval"
    assert response.operation == "developer_admin.grant"
