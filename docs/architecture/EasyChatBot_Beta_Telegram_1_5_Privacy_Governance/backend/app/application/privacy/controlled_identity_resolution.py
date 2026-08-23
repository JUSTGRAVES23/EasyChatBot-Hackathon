from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdentityResolutionRequest:
    pseudonymous_id: str
    reason: str
    approved_by: str


class ControlledIdentityResolution:
    def resolve(self, request: IdentityResolutionRequest) -> None:
        raise PermissionError(
            "Identity resolution requires approved governance workflow."
        )
