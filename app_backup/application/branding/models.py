"""
EasyChatBot branding models.

Defines immutable brand identity references.

Responsibilities:

- store approved brand metadata;
- provide shared identity references;
- support UI/reporting integrations.

This module does not:

- contain UI logic;
- load images;
- manage files;
- execute AI operations;
- influence Runtime behaviour.

Architecture:

Application Layer
        |
        v
Brand Identity Models
        |
        v
Presentation / Reporting Layers


Brand assets are immutable references.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrandIdentity:
    """
    Immutable EasyChatBot brand identity.

    Used by:

    - AI Operations Center;
    - reports;
    - emails;
    - documentation.
    """

    name: str

    tagline: str

    logo_asset: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "Brand name cannot be empty."
            )

        if not self.tagline.strip():
            raise ValueError(
                "Brand tagline cannot be empty."
            )

        if not self.logo_asset.strip():
            raise ValueError(
                "Logo asset reference cannot be empty."
            )


@dataclass(frozen=True)
class CharacterIdentity:
    """
    Immutable character identity reference.

    Characters belong to the presentation
    and experience layer.

    They must not affect business decisions.
    """

    character_id: str

    name: str

    asset_reference: str

    def __post_init__(self) -> None:
        if not self.character_id.strip():
            raise ValueError(
                "Character id cannot be empty."
            )

        if not self.name.strip():
            raise ValueError(
                "Character name cannot be empty."
            )

        if not self.asset_reference.strip():
            raise ValueError(
                "Character asset reference cannot be empty."
            )


EASYCHATBOT_BRAND = BrandIdentity(
    name="EasyChatBot",
    tagline="Growing With You.",
    logo_asset=(
        "Final Logo fixed version(10).png"
    ),
)


YETI_CHARACTER = CharacterIdentity(
    character_id="yeti",
    name="Yeti",
    asset_reference=(
        "Yeti models(8).png"
    ),
)