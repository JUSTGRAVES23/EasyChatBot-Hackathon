from __future__ import annotations

from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4

from app.application.developer_admin.developer_admin_service import (
    DeveloperAdminRecord,
    DeveloperAdminService,
)
from app.application.identity.transaction_authorization import (
    TransactionAuthorizationApplicationError,
    TransactionAuthorizationApplicationService,
)
from app.domain.identity.authentication_assurance import (
    AuthenticationAssuranceLevel,
)
from app.domain.identity.principal import Principal
from app.domain.identity.transaction_authorization import (
    CanonicalTransaction,
    TransactionAuthorization,
    TransactionAuthorizationDecision,
    TrustedApprovalEvidence,
)


class TrustedClock(Protocol):
    """Trusted application/server clock."""

    def now(self) -> datetime:
        ...


class DeveloperAdminTransactionService:
    """Application boundary for authorized Developer Admin mutations.

    Security flow:

        authenticated principal
            -> exact Developer Admin transaction
            -> pending user approval
            -> trusted assurance / approval
            -> exact transaction binding
            -> single-use consumption
            -> Developer Admin mutation

    The target is always extracted from the authorized canonical transaction.
    No execution request is allowed to replace the authorized target.
    """

    AUDIENCE = "easychatbot.developer_admin"

    GRANT_OPERATION = "developer_admin.grant"
    REVOKE_OPERATION = "developer_admin.revoke"

    REQUIRED_ASSURANCE_LEVEL = AuthenticationAssuranceLevel.A2
    DEFAULT_TRANSACTION_TTL = timedelta(minutes=5)

    def __init__(
        self,
        *,
        developer_admin_service: DeveloperAdminService,
        transaction_authorization_service: (
            TransactionAuthorizationApplicationService
        ),
        clock: TrustedClock,
    ) -> None:
        if developer_admin_service is None:
            raise ValueError("developer_admin_service is required.")

        if transaction_authorization_service is None:
            raise ValueError(
                "transaction_authorization_service is required."
            )

        if clock is None:
            raise ValueError("clock is required.")

        self._developer_admin_service = developer_admin_service
        self._transaction_authorization_service = (
            transaction_authorization_service
        )
        self._clock = clock

    def create_grant_transaction(
        self,
        *,
        principal: Principal,
        target_user_id: UUID,
        created_at: datetime | None = None,
        expires_at: datetime | None = None,
    ) -> TransactionAuthorization:
        return self._create_transaction(
            principal=principal,
            target_user_id=target_user_id,
            operation=self.GRANT_OPERATION,
            risk_operation="grant",
            created_at=created_at,
            expires_at=expires_at,
        )

    def create_revoke_transaction(
        self,
        *,
        principal: Principal,
        target_user_id: UUID,
        created_at: datetime | None = None,
        expires_at: datetime | None = None,
    ) -> TransactionAuthorization:
        return self._create_transaction(
            principal=principal,
            target_user_id=target_user_id,
            operation=self.REVOKE_OPERATION,
            risk_operation="revoke",
            created_at=created_at,
            expires_at=expires_at,
        )

    def _create_transaction(
        self,
        *,
        principal: Principal,
        target_user_id: UUID,
        operation: str,
        risk_operation: str,
        created_at: datetime | None,
        expires_at: datetime | None,
    ) -> TransactionAuthorization:
        self._require_valid_principal(principal)

        if not isinstance(target_user_id, UUID):
            raise ValueError("target_user_id must be a UUID.")

        effective_created_at = (
            created_at
            if created_at is not None
            else self._clock.now()
        )

        effective_expires_at = (
            expires_at
            if expires_at is not None
            else effective_created_at + self.DEFAULT_TRANSACTION_TTL
        )

        self._validate_transaction_times(
            created_at=effective_created_at,
            expires_at=effective_expires_at,
        )

        transaction = CanonicalTransaction.from_mapping(
            transaction_id=str(uuid4()),
            principal_id=principal.user_id,
            amount="0.00",
            currency="N/A",
            merchant_or_service="easychatbot",
            operation=operation,
            timestamp=effective_created_at,
            nonce=str(uuid4()),
            risk_context={
                "target_user_id": str(target_user_id),
                "operation": risk_operation,
                "audience": self.AUDIENCE,
            },
        )

        return (
            self._transaction_authorization_service.create_pending_authorization(
                principal=principal,
                transaction=transaction,
                authorization_id=str(uuid4()),
                created_at=effective_created_at,
                expires_at=effective_expires_at,
            )
        )

    def get_authorization(
        self,
        *,
        authorization_id: str,
    ) -> TransactionAuthorization | None:
        if not authorization_id:
            return None

        return self._transaction_authorization_service.registry.get(
            authorization_id
        )

    def attach_trusted_approval(
        self,
        *,
        principal: Principal,
        approval: TrustedApprovalEvidence,
    ) -> TransactionAuthorization:
        authorization = self.get_authorization(
            authorization_id=approval.authorization_id,
        )

        if authorization is None:
            raise TransactionAuthorizationApplicationError(
                "Transaction authorization was not found."
            )

        return self._transaction_authorization_service.attach_user_approval(
            principal=principal,
            authorization=authorization,
            approval=approval,
            clock=self._clock,
        )

    async def execute_grant(
        self,
        *,
        principal: Principal,
        authorization_id: str,
        transaction: CanonicalTransaction | None = None,
        clock: TrustedClock | None = None,
    ) -> DeveloperAdminRecord:
        authorization = self._resolve_execution_authorization(
            authorization_id=authorization_id,
            transaction=transaction,
            expected_operation=self.GRANT_OPERATION,
        )

        result = self._consume(
            principal=principal,
            authorization=authorization,
            clock=clock,
        )

        if result.decision is not TransactionAuthorizationDecision.ALLOW:
            raise PermissionError("transaction authorization denied")

        target_user_id = self._target_user_id_from_transaction(
            authorization.transaction,
            expected_operation=self.GRANT_OPERATION,
            expected_risk_operation="grant",
        )

        return await self._developer_admin_service.grant_developer_admin(
            actor=principal,
            user_id=target_user_id,
        )

    async def execute_revoke(
        self,
        *,
        principal: Principal,
        authorization_id: str,
        transaction: CanonicalTransaction | None = None,
        clock: TrustedClock | None = None,
    ) -> None:
        authorization = self._resolve_execution_authorization(
            authorization_id=authorization_id,
            transaction=transaction,
            expected_operation=self.REVOKE_OPERATION,
        )

        result = self._consume(
            principal=principal,
            authorization=authorization,
            clock=clock,
        )

        if result.decision is not TransactionAuthorizationDecision.ALLOW:
            raise PermissionError("transaction authorization denied")

        target_user_id = self._target_user_id_from_transaction(
            authorization.transaction,
            expected_operation=self.REVOKE_OPERATION,
            expected_risk_operation="revoke",
        )

        await self._developer_admin_service.revoke_developer_admin(
            actor=principal,
            user_id=target_user_id,
        )

    def _consume(
        self,
        *,
        principal: Principal,
        authorization: TransactionAuthorization,
        clock: TrustedClock | None,
    ):
        self._require_valid_principal(principal)

        return self._transaction_authorization_service.consume_authorization(
            principal=principal,
            authorization_id=authorization.authorization_id,
            expected_transaction=authorization.transaction,
            clock=clock if clock is not None else self._clock,
            required_assurance_level=self.REQUIRED_ASSURANCE_LEVEL,
        )

    def _resolve_execution_authorization(
        self,
        *,
        authorization_id: str,
        transaction: CanonicalTransaction | None,
        expected_operation: str,
    ) -> TransactionAuthorization:
        if not authorization_id:
            raise TransactionAuthorizationApplicationError(
                "Transaction authorization ID is required."
            )

        authorization = self.get_authorization(
            authorization_id=authorization_id,
        )

        if authorization is None:
            raise TransactionAuthorizationApplicationError(
                "Transaction authorization was not found."
            )

        if transaction is not None:
            if not isinstance(transaction, CanonicalTransaction):
                raise TransactionAuthorizationApplicationError(
                    "Canonical transaction is required."
                )

            if (
                transaction.canonical_representation()
                != authorization.transaction.canonical_representation()
            ):
                raise TransactionAuthorizationApplicationError(
                    "Canonical transaction binding mismatch."
                )

        self._target_user_id_from_transaction(
            authorization.transaction,
            expected_operation=expected_operation,
            expected_risk_operation=(
                "grant"
                if expected_operation == self.GRANT_OPERATION
                else "revoke"
            ),
        )

        return authorization

    def _target_user_id_from_transaction(
        self,
        transaction: CanonicalTransaction,
        *,
        expected_operation: str | None = None,
        expected_risk_operation: str | None = None,
    ) -> UUID:
        """Extract and validate the target exclusively from the transaction.

        When no expected operation is supplied, this helper defaults to the
        grant operation because the target-extraction contract is defined
        against the standard Developer Admin grant transaction.

        Execution paths always supply the explicit expected operation and
        risk operation, so grant and revoke cannot be substituted for one
        another.
        """
        if not isinstance(transaction, CanonicalTransaction):
            raise PermissionError("transaction is invalid")

        operation = (
            expected_operation
            if expected_operation is not None
            else self.GRANT_OPERATION
        )

        risk_operation = (
            expected_risk_operation
            if expected_risk_operation is not None
            else "grant"
        )

        if transaction.operation != operation:
            raise PermissionError(
                "transaction operation is invalid"
            )

        risk_context = dict(transaction.risk_context)

        if risk_context.get("operation") != risk_operation:
            raise PermissionError(
                "transaction risk operation is invalid"
            )

        if risk_context.get("audience") != self.AUDIENCE:
            raise PermissionError(
                "transaction audience is invalid"
            )

        target_value = risk_context.get("target_user_id")

        if not target_value:
            raise PermissionError(
                "transaction target is invalid"
            )

        try:
            return UUID(str(target_value))
        except (TypeError, ValueError, AttributeError) as exc:
            raise PermissionError(
                "transaction target is invalid"
            ) from exc

    @staticmethod
    def _require_valid_principal(
        principal: Principal,
    ) -> None:
        if principal is None:
            raise PermissionError(
                "authenticated principal is required"
            )

        if not principal.user_id:
            raise PermissionError(
                "authenticated principal is invalid"
            )

        if not principal.email_verified:
            raise PermissionError(
                "authenticated principal email is not verified"
            )

        account_status = getattr(
            principal,
            "account_status",
            None,
        )

        status_value = getattr(
            account_status,
            "value",
            account_status,
        )

        if status_value != "active":
            raise PermissionError(
                "authenticated principal is not active"
            )

    @staticmethod
    def _validate_transaction_times(
        *,
        created_at: datetime,
        expires_at: datetime,
    ) -> None:
        if created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware"
            )

        if expires_at.tzinfo is None:
            raise ValueError(
                "expires_at must be timezone-aware"
            )

        if expires_at <= created_at:
            raise ValueError(
                "expires_at must be later than created_at"
            )


__all__ = ["DeveloperAdminTransactionService"]