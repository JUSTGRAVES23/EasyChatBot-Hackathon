from __future__ import annotations

import inspect
from dataclasses import replace
from typing import Any

from .privacy_approval_email_service import (
    ApprovalEmailRequest,
    PrivacyApprovalEmailService,
)
from .privacy_change import (
    PrivacyChange,
    PrivacyChangeStatus,
)
from .privacy_change_registry import (
    PrivacyChangeRegistry,
)
from .privacy_validation_service import (
    PrivacyValidationService,
)


class PrivacyGovernanceGate:
    """Privacy governance decision gate.

    Responsibilities:
    - consume deterministic privacy validation results;
    - block changes with validation failures;
    - route privacy-impacting changes to DPO/GRC;
    - trigger an approval escalation only when validation passes;
    - never interpret email delivery as approval.

    Does NOT:
    - make legal decisions;
    - grant DPO/GRC approval;
    - execute production changes;
    - schedule recurring approval emails.

    Email delivery is notification infrastructure only.
    """

    def __init__(
        self,
        *,
        registry: PrivacyChangeRegistry,
        validation_service: PrivacyValidationService | None = None,
        approval_email_service: PrivacyApprovalEmailService | None = None,
    ) -> None:
        if registry is None:
            raise ValueError(
                "registry cannot be None."
            )

        self._registry = registry
        self._validation = validation_service
        self._approval_email = approval_email_service

    def route(
        self,
        change: PrivacyChange,
        *,
        automated_validation_passed: bool | None = None,
        dpo_approved: bool = False,
        grc_approved: bool = False,
    ) -> PrivacyChange:
        """Route a change through the synchronous governance decision."""

        if change is None:
            raise ValueError(
                "change cannot be None."
            )

        validation_passed = self._resolve_validation(
            automated_validation_passed
        )

        if not validation_passed:
            updated = replace(
                change,
                status=PrivacyChangeStatus.BLOCKED,
            )

        elif change.dpo_required or change.grc_required:
            dpo_ok = (
                not change.dpo_required
                or dpo_approved
            )

            grc_ok = (
                not change.grc_required
                or grc_approved
            )

            if dpo_ok and grc_ok:
                updated = replace(
                    change,
                    status=PrivacyChangeStatus.APPROVED,
                )
            else:
                updated = replace(
                    change,
                    status=PrivacyChangeStatus.PENDING_DPO_GRC,
                )

        else:
            updated = replace(
                change,
                status=PrivacyChangeStatus.APPROVED,
            )

        self._save(updated)

        return updated

    async def route_and_escalate(
        self,
        change: PrivacyChange,
    ) -> PrivacyChange:
        """Run automated validation and escalate when required.

        Email is sent only when:

        1. automated privacy validation passes;
        2. the change requires DPO/GRC review;
        3. the change is not already approved.

        Email delivery never changes governance status to APPROVED.
        """

        if change is None:
            raise ValueError(
                "change cannot be None."
            )

        if self._validation is None:
            raise RuntimeError(
                "PrivacyValidationService is required "
                "for automatic governance routing."
            )

        if self._approval_email is None:
            raise RuntimeError(
                "PrivacyApprovalEmailService is required "
                "for automatic governance escalation."
            )

        validation = self._validation.validate()

        if validation.status != "PASS":
            updated = replace(
                change,
                status=PrivacyChangeStatus.BLOCKED,
            )

            self._save(updated)

            return updated

        if not (
            change.dpo_required
            or change.grc_required
        ):
            updated = replace(
                change,
                status=PrivacyChangeStatus.APPROVED,
            )

            self._save(updated)

            return updated

        updated = replace(
            change,
            status=PrivacyChangeStatus.PENDING_DPO_GRC,
        )

        self._save(updated)

        # --------------------------------------------------------------
        # Application-level escalation
        # --------------------------------------------------------------

        request = self._approval_email.escalate(
            change=updated,
            validation_passed=True,
        )

        # --------------------------------------------------------------
        # Await asynchronous infrastructure delivery
        # --------------------------------------------------------------
        #
        # PrivacyApprovalEmailService deliberately remains synchronous
        # for application compatibility.
        #
        # When its sender is asynchronous, the resulting awaitable is
        # carried by ApprovalEmailRequest.delivery.
        #
        # This gate is async, so it is the correct boundary at which
        # that infrastructure operation is awaited.
        #

        delivery = getattr(
            request,
            "delivery",
            None,
        )

        if inspect.isawaitable(delivery):
            delivery_result = await delivery
            self._validate_email_result(
                delivery_result
            )
        else:
            self._validate_email_result(
                request
            )

        # --------------------------------------------------------------
        # GOVERNANCE INVARIANT
        # --------------------------------------------------------------
        #
        # Email delivery is never approval.
        #
        # The change remains PENDING_DPO_GRC until the explicit human
        # governance decision is recorded.
        #

        return updated

    def can_proceed(
        self,
        change_id: str,
    ) -> bool:
        """Return True only when a valid change ID is explicitly approved."""

        if not isinstance(change_id, str):
            raise ValueError(
                "change_id is required."
            )

        normalized_change_id = change_id.strip()

        if not normalized_change_id:
            raise ValueError(
                "change_id is required."
            )

        change = self._registry.get(
            normalized_change_id
        )

        return bool(
            change
            and change.status
            == PrivacyChangeStatus.APPROVED
        )

    def _resolve_validation(
        self,
        explicit_result: bool | None,
    ) -> bool:
        """Resolve automated validation."""

        if self._validation is not None:
            result = self._validation.validate()

            return (
                result.status == "PASS"
            )

        if explicit_result is None:
            raise ValueError(
                "automated_validation_passed is required "
                "when no PrivacyValidationService is configured."
            )

        return explicit_result

    def _save(
        self,
        change: PrivacyChange,
    ) -> None:
        """Persist the authoritative PrivacyChange."""

        existing = self._registry.get(
            change.change_id
        )

        if existing is None:
            self._registry.register(
                change
            )
        else:
            self._registry.update(
                change
            )

    @staticmethod
    def _validate_email_result(
        result: Any,
    ) -> None:
        """Validate email delivery metadata.

        Supported results:

        - ``None``
        - ``ApprovalEmailRequest``
        - provider result dictionaries

        None of these represents governance approval.
        """

        if result is None:
            return

        if isinstance(
            result,
            ApprovalEmailRequest,
        ):
            return

        if isinstance(
            result,
            dict,
        ):
            return

        raise TypeError(
            "Email provider returned an invalid result."
        )


__all__ = [
    "PrivacyGovernanceGate",
]