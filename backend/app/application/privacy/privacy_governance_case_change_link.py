from __future__ import annotations

from dataclasses import dataclass

from .privacy_change import PrivacyChange
from .privacy_change_registry import PrivacyChangeRegistry
from .privacy_governance_case import PrivacyGovernanceCase
from .privacy_governance_case_registry import PrivacyGovernanceCaseRegistry


@dataclass(frozen=True, slots=True)
class PrivacyGovernanceCaseChangeLink:
    """Resolved relationship between one governance case and its change.

    The case's ``change_id`` is resolved against the authoritative
    PrivacyChangeRegistry.

    This object is a read-only application projection used by reporting,
    governance evidence, and Excel synchronization.

    It does not create or maintain a second relationship store.
    """

    case: PrivacyGovernanceCase
    change: PrivacyChange


class PrivacyGovernanceCaseChangeLinkService:
    """Resolve and validate Case -> PrivacyChange traceability.

    A governance case must remain traceable to the privacy change that
    caused it.

    The authoritative relationship is:

        PrivacyGovernanceCase.change_id
                    ↓
        PrivacyChangeRegistry
                    ↓
             PrivacyChange

    The service is deliberately read-only.
    """

    def __init__(
        self,
        *,
        case_registry: PrivacyGovernanceCaseRegistry,
        change_registry: PrivacyChangeRegistry,
    ) -> None:
        if case_registry is None:
            raise ValueError(
                "case_registry cannot be None."
            )

        if change_registry is None:
            raise ValueError(
                "change_registry cannot be None."
            )

        self._cases = case_registry
        self._changes = change_registry

    def get_change_for_case(
        self,
        case_id: str,
    ) -> PrivacyChange:
        """Return the authoritative PrivacyChange for a governance case."""

        case = self.get_case(case_id)

        return self._get_change(case)

    def get_link(
        self,
        case_id: str,
    ) -> PrivacyGovernanceCaseChangeLink:
        """Resolve a complete case-to-change relationship."""

        case = self.get_case(case_id)

        change = self._get_change(case)

        return PrivacyGovernanceCaseChangeLink(
            case=case,
            change=change,
        )

    def list_links(
        self,
    ) -> tuple[PrivacyGovernanceCaseChangeLink, ...]:
        """Resolve all registered case-to-change relationships."""

        return tuple(
            PrivacyGovernanceCaseChangeLink(
                case=case,
                change=self._get_change(case),
            )
            for case in self._cases.all()
        )

    def get_case(
        self,
        case_id: str,
    ) -> PrivacyGovernanceCase:
        """Return a governance case by identifier."""

        if (
            not isinstance(case_id, str)
            or not case_id.strip()
        ):
            raise ValueError(
                "case_id is required."
            )

        return self._cases.get(case_id)

    def _get_change(
        self,
        case: PrivacyGovernanceCase,
    ) -> PrivacyChange:
        """Resolve the authoritative change for a case.

        PrivacyChangeRegistry.get() returns None when the change does not
        exist. The link service converts that into an explicit KeyError so
        missing Case -> Change relationships cannot silently pass through.
        """

        change_id = getattr(
            case,
            "change_id",
            None,
        )

        if (
            not isinstance(change_id, str)
            or not change_id.strip()
        ):
            raise ValueError(
                "Governance case has no "
                f"change_id relationship: {case.case_id}"
            )

        change = self._changes.get(
            change_id
        )

        if change is None:
            raise KeyError(
                "Privacy change not found for "
                f"governance case {case.case_id}: "
                f"{change_id}"
            )

        return change


__all__ = [
    "PrivacyGovernanceCaseChangeLink",
    "PrivacyGovernanceCaseChangeLinkService",
]