from __future__ import annotations

from unittest.mock import Mock, patch

from app.application.composition.beta_telegram_production import (
    BetaTelegramProductionComposition,
    create_production_beta_telegram_composition,
)
from app.application.world_catalogue.service import LearningWorldCatalogueService
from tests.application.composition.deterministic_language_detector import (
    DeterministicLanguageDetector,
)


def test_production_composition_wires_catalogue_service_to_shared_world_resolver():
    engine = Mock(name="database_engine")
    session_factory = Mock(name="session_factory")
    functionality_control = Mock(name="functionality_control")
    captured: dict[str, object] = {}

    beta_telegram = Mock(name="beta_telegram")

    def fake_create_beta_telegram_composition(**kwargs):
        captured.update(kwargs)
        return beta_telegram

    with patch(
        "app.application.composition.beta_telegram_production."
        "create_beta_telegram_composition",
        side_effect=fake_create_beta_telegram_composition,
    ):
        composition = create_production_beta_telegram_composition(
            database_engine=engine,
            session_factory=session_factory,
            functionality_control_service=functionality_control,
            language_detector=DeterministicLanguageDetector(),
        )

    assert isinstance(composition, BetaTelegramProductionComposition)
    assert isinstance(
        composition.catalogue_service,
        LearningWorldCatalogueService,
    )

    shared_resolver = captured["world_resolver"]

    assert (
        composition.catalogue_service._world_resolver
        is shared_resolver
    )

    assert captured["world_resolver"] is composition.catalogue_service._world_resolver

