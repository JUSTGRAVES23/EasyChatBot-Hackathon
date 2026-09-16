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
)


class TrustedClock(Protocol):
    """Trusted application/server clock."""

    def now(self) -> datetime:
        ...


class DeveloperAdminTransactionService:
    """
    Application service protecting Developer Admin mutations with
    transaction authorization.

    Security flow:

        authenticated principal
            -> exact Developer Admin transaction
            -> pending user approval
            -> trusted assurance / approval
            -> exact transaction binding
            -> single-use consumption
            -> Developer Admin mutation

    The target user is never taken from the execution request after the
    transaction has been authorized. The execution target is extracted from
    the exact canonical transaction that is being consumed.
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
        """
        Create an exact Developer Admin grant authorization.

        The authorization ID is generated here and passed explicitly to the
        transaction-authorization application service because that service
        requires the authorization identifier as part of its contract.

        The target user ID is embedded into the canonical transaction and is
        therefore part of the transaction binding.
        """

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

        authorization_id = str(uuid4())

        transaction = CanonicalTransaction.from_mapping(
            transaction_id=str(uuid4()),
            principal_id=principal.user_id,
            amount="0.00",
            currency="N/A",
            merchant_or_service="easychatbot",
            operation=self.GRANT_OPERATION,
            timestamp=effective_created_at,
            nonce=str(uuid4()),
            risk_context={
                "target_user_id": str(target_user_id),
                "operation": "grant",
                "audience": self.AUDIENCE,
            },
        )

        return (
            self._transaction_authorization_service
            .create_pending_authorization(
                principal=principal,
                transaction=transaction,
                authorization_id=authorization_id,
                created_at=effective_created_at,
                expires_at=effective_expires_at,
            )
        )

    async def execute_grant(
        self,
        *,
        principal: Principal,
        authorization_id: str,
        transaction: CanonicalTransaction,
        clock: TrustedClock | None = None,
    ) -> DeveloperAdminRecord:
        """
        Execute a previously authorized Developer Admin grant.

        Execution requires:

        - authenticated principal
        - exact authorization ID
        - exact canonical transaction binding
        - A2 authentication assurance
        - single-use authorization consumption

        The target user is extracted exclusively from the authorized
        transaction.
        """

        self._require_valid_principal(principal)

        if not authorization_id:
            raise TransactionAuthorizationApplicationError(
                "Transaction authorization ID is required."
            )

        if not isinstance(transaction, CanonicalTransaction):
            raise TransactionAuthorizationApplicationError(
                "Canonical transaction is required."
            )

        execution_clock = (
            clock
            if clock is not None
            else self._clock
        )

        self._validate_expected_grant_transaction(transaction)

        result = (
            self._transaction_authorization_service
            .consume_authorization(
                principal=principal,
                authorization_id=authorization_id,
                expected_transaction=transaction,
                clock=execution_clock,
                required_assurance_level=(
                    self.REQUIRED_ASSURANCE_LEVEL
                ),
            )
        )

        if result.decision is not TransactionAuthorizationDecision.ALLOW:
            raise PermissionError("transaction authorization denied")

        target_user_id = self._target_user_id_from_transaction(
            transaction
        )

        return await self._developer_admin_service.grant_developer_admin(
            actor=principal,
            user_id=target_user_id,
        )

    def _target_user_id_from_transaction(
        self,
        transaction: CanonicalTransaction,
    ) -> UUID:
        """
        Extract the target from an authorized Developer Admin grant
        transaction.

        This helper is intentionally strict.

        It is a grant execution helper, therefore a revoke transaction,
        even if otherwise structurally valid, must never be accepted here.
        """

        if not isinstance(transaction, CanonicalTransaction):
            raise PermissionError("transaction target is invalid")

        if transaction.operation != self.GRANT_OPERATION:
            raise PermissionError("transaction operation is invalid")

        risk_context = dict(transaction.risk_context)

        if risk_context.get("operation") != "grant":
            raise PermissionError("transaction operation is invalid")

        if risk_context.get("audience") != self.AUDIENCE:
            raise PermissionError("transaction audience is invalid")

        target_value = risk_context.get("target_user_id")

        if not target_value:
            raise PermissionError("transaction target is invalid")

        try:
            return UUID(str(target_value))
        except (TypeError, ValueError, AttributeError) as exc:
            raise PermissionError(
                "transaction target is invalid"
            ) from exc

    def _validate_expected_grant_transaction(
        self,
        transaction: CanonicalTransaction,
    ) -> None:
        """
        Validate the structural contract of a Developer Admin grant
        transaction before consuming its authorization.
        """

        if transaction.operation != self.GRANT_OPERATION:
            raise PermissionError("transaction operation is invalid")

        risk_context = dict(transaction.risk_context)

        if risk_context.get("operation") != "grant":
            raise PermissionError("transaction operation is invalid")

        if risk_context.get("audience") != self.AUDIENCE:
            raise PermissionError("transaction audience is invalid")

        self._target_user_id_from_transaction(transaction)

    @staticmethod
    def _require_valid_principal(
        principal: Principal,
    ) -> None:
        """
        Require the normal authenticated-principal contract.

        This does not derive authentication assurance and must not be used
        as a substitute for W15.6 assurance evidence.
        """

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


__all__ = [
    "DeveloperAdminTransactionService",
]