from __future__ import annotations

from dataclasses import replace

from .privacy_approval_email_service import (
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
        """Route a change through the governance decision.

        This synchronous method preserves the existing Beta contract.

        If a validation service is configured, it is the authoritative
        source for automated privacy validation.
        """

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
            if not (
                dpo_approved
                and grc_approved
            ):
                updated = replace(
                    change,
                    status=(
                        PrivacyChangeStatus.PENDING_DPO_GRC
                    ),
                )
            else:
                updated = replace(
                    change,
                    status=(
                        PrivacyChangeStatus.APPROVED
                    ),
                )

        else:
            updated = replace(
                change,
                status=(
                    PrivacyChangeStatus.APPROVED
                ),
            )

        self._save(updated)

        return updated

    async def route_and_escalate(
        self,
        change: PrivacyChange,
    ) -> PrivacyChange:
        """Run automated validation and escalate when governance requires it.

        Email is sent ONLY when:

        1. PrivacyValidationService returns PASS;
        2. the change requires DPO/GRC review;
        3. the change is not already approved.

        Email delivery never changes the governance status to APPROVED.
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
            status=(
                PrivacyChangeStatus.PENDING_DPO_GRC
            ),
        )

        self._save(updated)

        self._approval_email.escalate(
    change=updated,
    validation_passed=True,
)

        return updated

    def can_proceed(
        self,
        change_id: str,
    ) -> bool:
        change = self._registry.get(
            change_id
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