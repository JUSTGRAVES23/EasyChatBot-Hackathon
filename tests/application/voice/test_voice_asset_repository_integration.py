"""
===============================================================================

File
----
tests/application/voice/test_voice_asset_repository_integration.py


Purpose
-------
Regression tests for voice asset repository integration.


Architecture Flow
-----------------

Voice Registry

        |

        v

Voice Asset Repository

        |

        v

Voice Runtime / Generation


Validated Behaviour
-------------------

✓ Voice assets can be stored

✓ Voice assets can be retrieved

✓ Character identity is preserved

✓ Language versioning is preserved

✓ Provider references are preserved

✓ Missing assets fail safely


Engineering Principles
----------------------

- Clean Architecture
- Repository abstraction
- Asset traceability
- Provider independence


===============================================================================
"""


from __future__ import annotations


from dataclasses import dataclass





# ============================================================================
# Domain Simulation
# ============================================================================


@dataclass(frozen=True)
class VoiceAsset:

    asset_id: str

    character_id: str

    language_code: str

    voice_identity_id: str

    provider_name: str

    version: str

    artifact_uri: str





# ============================================================================
# Repository Simulation
# ============================================================================


class FakeVoiceAssetRepository:
    """
    Voice asset persistence boundary.
    """


    def __init__(self):

        self.assets = {}



    def save(
        self,
        asset: VoiceAsset,
    ):

        self.assets[

            asset.asset_id

        ] = asset



    def get(
        self,
        asset_id: str,
    ):

        return self.assets.get(
            asset_id
        )





# ============================================================================
# Application Service
# ============================================================================


class VoiceAssetRepositoryService:
    """
    Application service coordinating
    voice asset storage and retrieval.
    """


    def __init__(
        self,
        *,
        repository,
    ):

        self._repository = repository



    def register_asset(
        self,
        *,
        asset: VoiceAsset,
    ):

        self._repository.save(
            asset
        )

        return asset



    def retrieve_asset(
        self,
        *,
        asset_id: str,
    ):


        asset = self._repository.get(
            asset_id
        )


        if asset is None:

            raise ValueError(
                "Voice asset not found."
            )


        return asset





# ============================================================================
# Fixtures
# ============================================================================


def create_service():


    repository = FakeVoiceAssetRepository()


    service = VoiceAssetRepositoryService(

        repository=repository,

    )


    return service





def create_asset():


    return VoiceAsset(

        asset_id="asset-clara-fr-v1",

        character_id="clara",

        language_code="fr-FR",

        voice_identity_id="voice-clara-fr",

        provider_name="openai",

        version="v1",

        artifact_uri=(
            "storage://voices/clara/fr/v1"
        ),

    )





# ============================================================================
# Tests
# ============================================================================


def test_voice_asset_can_be_registered():


    service = create_service()


    result = service.register_asset(

        asset=create_asset()

    )


    assert result.asset_id == (
        "asset-clara-fr-v1"
    )


    assert result.character_id == (
        "clara"
    )





def test_voice_asset_can_be_retrieved():


    service = create_service()


    service.register_asset(

        asset=create_asset()

    )


    result = service.retrieve_asset(

        asset_id="asset-clara-fr-v1"

    )


    assert result.voice_identity_id == (

        "voice-clara-fr"

    )





def test_asset_preserves_language_information():


    service = create_service()


    service.register_asset(

        asset=create_asset()

    )


    result = service.retrieve_asset(

        asset_id="asset-clara-fr-v1"

    )


    assert result.language_code == (

        "fr-FR"

    )


    assert result.version == "v1"





def test_asset_preserves_provider_reference():


    service = create_service()


    service.register_asset(

        asset=create_asset()

    )


    result = service.retrieve_asset(

        asset_id="asset-clara-fr-v1"

    )


    assert result.provider_name == (

        "openai"

    )





def test_missing_voice_asset_fails_safely():


    service = create_service()


    try:

        service.retrieve_asset(

            asset_id="missing"

        )


        assert False, (

            "Expected missing asset failure."

        )


    except ValueError as exc:

        assert (

            "not found"

            in

            str(exc).lower()

        )