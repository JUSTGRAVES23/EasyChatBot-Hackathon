"""
Operations Center presentation models.

YETI is a governance assistant only.
It explains operational state and audit evidence.
It has no authority to change controls.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class OperationsCenterBrand:
    product_name: str = "EasyChatBot Operations Center"
    mascot: str = "YETI"
    mascot_role: str = "Governance Assistant"
    font_family: str = "Nunito"
    character_font: str = "Fredoka"
    accent_font: str = "Caveat"


@dataclass(frozen=True)
class YetiGovernanceMessage:
    """
    Human-readable governance explanation.

    This is presentation data only. It cannot pause,
    resume, approve, or execute any system action.
    """

    message: str
    severity: str
    component: str
    action_required: bool
