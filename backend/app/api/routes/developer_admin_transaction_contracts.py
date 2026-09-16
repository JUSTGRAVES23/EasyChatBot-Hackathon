from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DeveloperAdminCreateTransactionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_user_id: UUID


class DeveloperAdminPendingTransactionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authorization_id: str
    transaction_id: str
    operation: str
    audience: str
    target_user_id: UUID
    state: str
    expires_at: datetime


class DeveloperAdminApprovalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authorization_id: str
    transaction_id: str
    state: str
    expires_at: datetime


class DeveloperAdminExecuteTransactionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authorization_id: str
    state: str


__all__ = [
    "DeveloperAdminApprovalResponse",
    "DeveloperAdminCreateTransactionRequest",
    "DeveloperAdminExecuteTransactionResponse",
    "DeveloperAdminPendingTransactionResponse",
]
