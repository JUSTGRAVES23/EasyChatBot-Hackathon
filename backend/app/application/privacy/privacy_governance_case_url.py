from __future__ import annotations

from urllib.parse import quote


class PrivacyGovernanceCaseURLBuilder:
    """Build stable application URLs for human governance review."""

    def __init__(self, *, app_base_url: str) -> None:
        base = app_base_url.strip().rstrip("/")

        if not base:
            raise ValueError("app_base_url is required.")

        self._base_url = base

    def build(self, case_id: str) -> str:
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError("case_id is required.")

        return (
            f"{self._base_url}/privacy-governance/"
            f"{quote(case_id.strip(), safe='')}"
        )


__all__ = [
    "PrivacyGovernanceCaseURLBuilder",
]