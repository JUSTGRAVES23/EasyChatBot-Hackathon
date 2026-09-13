from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.application.authorization.authorization_service import (
    AuthorizationService,
)
from app.domain.identity.authentication_assurance import (
    AuthenticationAssuranceContext,
    AuthenticationAssuranceLevel,
    TrustedClock,
)
from app.domain.identity.principal import Principal
from app.domain.identity.transaction_authorization import (
    CanonicalTransaction,
    TransactionAuthorization,
    TransactionAuthorizationConsumer,
    TransactionAuthorizationDecisionResult,
    TransactionAuthorizationRegistry,
    TransactionAuthorizationState,
    TrustedApprovalEvidence,
    attach_approval,
    transition,
)


class TransactionAuthorizationApplicationError(RuntimeError):
    """Application-layer transaction-authorization failure."""


@dataclass(frozen=True, slots=True)
class TransactionAuthorizationApplicationService:
    """Application boundary for transaction authorization.

    Coordinates authenticated-principal validation, domain transaction
    authorization, assurance-context consumption, and atomic consumption.

    This service does not implement authentication, security-factor
    management, external identity integration, authentication freshness
    policy, business authorization policy, payment execution, money movement,
    or cryptographic transaction signing.

    W15.7 consumes the W15.6 AuthenticationAssuranceContext.
    """

    authorization_service: AuthorizationService
    registry: TransactionAuthorizationRegistry
    consumer: TransactionAuthorizationConsumer

    def require_authorized_principal(
        self,
        *,
        principal: Principal,
    ) -> Principal:
        """Require an authenticated and active principal."""
        return self.authorization_service.require_authenticated(principal)

    def create_pending_authorization(
        self,
        *,
        principal: Principal,
        transaction: CanonicalTransaction,
        authorization_id: str,
        created_at: datetime,
        expires_at: datetime,
    ) -> TransactionAuthorization:
        """Create and register a pending transaction authorization."""
        authenticated = self.require_authorized_principal(
            principal=principal,
        )

        if transaction.principal_id != authenticated.user_id:
            raise TransactionAuthorizationApplicationError(
                "Transaction principal does not match authenticated principal."
            )

        authorization = TransactionAuthorization(
            authorization_id=authorization_id,
            transaction=transaction,
            created_at=created_at,
            expires_at=expires_at,
        )

        pending = transition(
            authorization,
            TransactionAuthorizationState.PENDING_USER_APPROVAL,
        )

        self.registry.register(pending)

        return pending

    def attach_user_approval(
        self,
        *,
        principal: Principal,
        authorization: TransactionAuthorization,
        approval: TrustedApprovalEvidence,
        clock: TrustedClock,
    ) -> TransactionAuthorization:
        """Attach trusted approval to the exact pending transaction.

        Assurance is consumed from the W15.6 AuthenticationAssuranceContext.
        W15.7 does not derive or recreate authentication assurance.
        """
        authenticated = self.require_authorized_principal(
            principal=principal,
        )

        if authorization.transaction.principal_id != authenticated.user_id:
            raise TransactionAuthorizationApplicationError(
                "Transaction principal does not match authenticated principal."
            )

        if approval.transaction.principal_id != authenticated.user_id:
            raise TransactionAuthorizationApplicationError(
                "Approval principal does not match authenticated principal."
            )

        if not isinstance(
            approval.assurance_context,
            AuthenticationAssuranceContext,
        ):
            raise TransactionAuthorizationApplicationError(
                "W15.6 AuthenticationAssuranceContext is required."
            )

        if approval.assurance_context.principal_id != authenticated.user_id:
            raise TransactionAuthorizationApplicationError(
                "Authentication assurance principal does not match "
                "authenticated principal."
            )

        if not isinstance(
            approval.assurance_context.assurance_level,
            AuthenticationAssuranceLevel,
        ):
            raise TransactionAuthorizationApplicationError(
                "Authentication assurance level is invalid."
            )

        approved = attach_approval(
            authorization,
            approval,
            clock=clock,
        )

        # TransactionAuthorization is immutable. Replace the pending
        # snapshot in the trusted registry with the approved snapshot.
        # Compare-and-swap prevents overwriting a concurrent state change.
        replaced = self.registry.replace(
            authorization.authorization_id,
            authorization,
            approved,
        )

        if not replaced:
            raise TransactionAuthorizationApplicationError(
                "Transaction authorization state changed concurrently."
            )

        return approved

    def consume_authorization(
        self,
        *,
        principal: Principal,
        authorization_id: str,
        expected_transaction: CanonicalTransaction,
        clock: TrustedClock,
        required_assurance_level: AuthenticationAssuranceLevel,
    ) -> TransactionAuthorizationDecisionResult:
        """Atomically consume one exact transaction authorization."""
        authenticated = self.require_authorized_principal(
            principal=principal,
        )

        if expected_transaction.principal_id != authenticated.user_id:
            raise TransactionAuthorizationApplicationError(
                "Transaction principal does not match authenticated principal."
            )

        if not isinstance(
            required_assurance_level,
            AuthenticationAssuranceLevel,
        ):
            raise TransactionAuthorizationApplicationError(
                "Required authentication assurance level is invalid."
            )

        return self.consumer.consume_once(
            authorization_id,
            expected_transaction=expected_transaction,
            clock=clock,
            required_assurance_level=required_assurance_level,
        )


__all__ = [
    "TransactionAuthorizationApplicationError",
    "TransactionAuthorizationApplicationService",
]
