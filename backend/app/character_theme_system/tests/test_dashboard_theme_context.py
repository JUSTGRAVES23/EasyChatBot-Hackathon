from pathlib import Path

from app.character_theme_system.application.dashboard_theme_context import (
    DashboardThemeContextBuilder,
)
from app.character_theme_system.application.theme_resolver import (
    CharacterThemeResolver,
)
from app.character_theme_system.configuration.theme_loader import (
    CharacterThemeLoader,
)
from app.character_theme_system.infrastructure.file_theme_repository import (
    FileThemeRepository,
)
from app.character_theme_system.presentation.theme_adapter import (
    DashboardThemeAdapter,
)


def test_dashboard_context_is_serialisable(tmp_path: Path) -> None:
    (tmp_path / "alix.yaml").write_text(
        """
id: alix
name: Alix
theme_version: "1.0"

theme:
  accent:
    primary: "#E91E63"

worlds:
  france:
    background:
      landmark: eiffel_tower
""",
        encoding="utf-8",
    )

    loader = CharacterThemeLoader(
        repository=FileThemeRepository(
            themes_directory=tmp_path
        )
    )

    resolver = CharacterThemeResolver(
        loader=loader
    )

    builder = DashboardThemeContextBuilder(
        resolver=resolver
    )

    context = builder.build(
        character_id="alix",
        world_id="france",
        primary_language="fr",
        secondary_language="es",
    )

    adapted = DashboardThemeAdapter().adapt(context)

    assert adapted["character"]["id"] == "alix"
    assert adapted["world"]["id"] == "france"
    assert adapted["languages"]["primary"] == "fr"
    assert adapted["languages"]["secondary"] == "es"
    assert (
        adapted["theme"]["worlds"]["france"]["background"]["landmark"]
        == "eiffel_tower"
    )
