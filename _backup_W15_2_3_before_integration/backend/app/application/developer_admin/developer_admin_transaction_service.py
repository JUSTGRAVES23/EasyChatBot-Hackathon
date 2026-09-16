from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from app.application.developer_admin.developer_admin_service import (
    DeveloperAdminRecord,
    DeveloperAdminService,
)
from app.application.identity.transaction_authorization import (
    TransactionAuthorizationApplicationService,
)
from app.domain.identity.authentication_assurance import (
    AuthenticationAssuranceLevel,
    TrustedClock,
)
from app.domain.identity.principal import Principal
from app.domain.identity.transaction_authorization import (
    CanonicalTransaction,
    TransactionAuthorizationDecision,
)


@dataclass(frozen=True, slots=True)
class DeveloperAdminTransactionRequest:
    """Exact transaction request for a Developer Administrator mutation."""

    operation: str
    target_user_id: UUID


class DeveloperAdminTransactionService:
    """
    Security orchestration boundary for Developer Administrator mutations.

    This service deliberately does not manufacture authentication assurance.
    A real trusted approval/evidence source must provide the approval before
    the underlying Developer Admin mutation is executed.

    The exact target user is bound into the canonical transaction security
    context so that the authorization applies to the intended mutation.
    """

    AUDIENCE = "easychatbot.developer_admin"
    REQUIRED_ASSURANCE_LEVEL = AuthenticationAssuranceLevel.A2
    GRANT_OPERATION = "developer_admin.grant"

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
        created_at: datetime,
        expires_at: datetime,
    ):
        """
        Create a pending Developer Administrator grant authorization.

        The target user ID is included in the canonical transaction's
        security-relevant risk context. The transaction authorization layer
        is responsible for registering and enforcing the exact transaction
        binding.
        """
        transaction = CanonicalTransaction.from_mapping(
            transaction_id=str(uuid4()),
            principal_id=principal.user_id,
            amount="0.00",
            currency="N/A",
            merchant_or_service="easychatbot",
            operation=self.GRANT_OPERATION,
            timestamp=created_at,
            nonce=str(uuid4()),
            risk_context={
                "target_user_id": str(target_user_id),
                "operation": "grant",
                "audience": self.AUDIENCE,
            },
        )

        return (
            self._transaction_authorization_service.create_pending_authorization(
                principal=principal,
                transaction=transaction,
                authorization_id=str(uuid4()),
                created_at=created_at,
                expires_at=expires_at,
            )
        )

    async def execute_grant(
        self,
        *,
        principal: Principal,
        authorization_id: str,
        transaction: CanonicalTransaction,
        clock: TrustedClock,
    ) -> DeveloperAdminRecord:
        """
        Consume the exact authorization and execute the Developer Admin grant.

        The mutation target is derived exclusively from the authorized
        canonical transaction. A second caller-controlled target_user_id is
        deliberately not accepted.

        The mutation is executed only after transaction authorization allows
        the exact transaction at the required authentication-assurance level.
        """
        target_user_id = self._target_user_id_from_transaction(transaction)

        decision = (
            self._transaction_authorization_service.consume_authorization(
                principal=principal,
                authorization_id=authorization_id,
                expected_transaction=transaction,
                clock=clock,
                required_assurance_level=self.REQUIRED_ASSURANCE_LEVEL,
            )
        )

        if decision.decision is not TransactionAuthorizationDecision.ALLOW:
            raise PermissionError(
                "Developer Administrator transaction authorization denied."
            )

        return await self._developer_admin_service.grant_developer_admin(
            actor=principal,
            user_id=target_user_id,
        )

    @classmethod
    def _target_user_id_from_transaction(
        cls,
        transaction: CanonicalTransaction,
    ) -> UUID:
        """
        Extract and validate the mutation target from the canonical
        transaction security context.

        This prevents the authorization decision from being applied to a
        different caller-supplied target.
        """
        if transaction.operation != cls.GRANT_OPERATION:
            raise PermissionError(
                "Developer Administrator transaction operation is invalid."
            )

        risk_context = dict(transaction.risk_context)

        if risk_context.get("audience") != cls.AUDIENCE:
            raise PermissionError(
                "Developer Administrator transaction audience is invalid."
            )

        if risk_context.get("operation") != "grant":
            raise PermissionError(
                "Developer Administrator transaction operation context is invalid."
            )

        raw_target_user_id = risk_context.get("target_user_id")

        if not isinstance(raw_target_user_id, str):
            raise PermissionError(
                "Developer Administrator transaction target is invalid."
            )

        try:
            return UUID(raw_target_user_id)
        except ValueError as exc:
            raise PermissionError(
                "Developer Administrator transaction target is invalid."
            ) from exc


__all__ = [
    "DeveloperAdminTransactionRequest",
    "DeveloperAdminTransactionService",
]