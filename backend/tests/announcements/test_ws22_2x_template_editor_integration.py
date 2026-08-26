from __future__ import annotations

import pytest

from backend.app.application.announcements.publication_service import (
    AnnouncementPublicationService,
)
from backend.app.application.announcements.template_editor_service import (
    AnnouncementTemplateEditorService,
)
from backend.app.application.announcements.template_registry import (
    AnnouncementTemplateRegistry,
)
from backend.app.domain.announcements.template_models import (
    AnnouncementTemplate,
    AnnouncementTemplateVersion,
    PublicationType,
)
from backend.app.infrastructure.announcements.in_memory_repositories import (
    InMemoryAnnouncementTemplateRepository,
    InMemoryPublicationRepository,
)


def make_editor() -> AnnouncementTemplateEditorService:
    templates = InMemoryAnnouncementTemplateRepository()
    templates.save(
        AnnouncementTemplate(
            template_id="beta-update",
            name="Beta Update",
            publication_type=PublicationType.BETA_UPDATE,
            active_version=2,
            description="Official Beta update pattern.",
            category="Beta",
            versions=(
                AnnouncementTemplateVersion(
                    template_id="beta-update",
                    version=2,
                    publication_type=PublicationType.BETA_UPDATE,
                    structure=(
                        "EASYCHATBOT ACADEMY",
                        "",
                        "{{headline}}",
                        "",
                        "{{body}}",
                        "",
                        "{{timing}}",
                    ),
                    required_fields=frozenset({"headline", "body"}),
                    optional_fields=frozenset({"timing"}),
                ),
            ),
        )
    )

    registry = AnnouncementTemplateRegistry(templates)
    publications = InMemoryPublicationRepository()
    publication_service = AnnouncementPublicationService(
        templates=registry,
        publications=publications,
    )

    return AnnouncementTemplateEditorService(
        templates=registry,
        publications=publication_service,
    )


def test_editor_lists_human_readable_approved_templates() -> None:
    editor = make_editor()

    items = editor.list_approved_templates()

    assert len(items) == 1
    assert items[0].name == "Beta Update"
    assert items[0].category == "Beta"
    assert items[0].description == "Official Beta update pattern."
    assert items[0].version == 2
    assert [field.name for field in items[0].fields] == [
        "body",
        "headline",
        "timing",
    ]


def test_editor_preview_uses_selected_template_version() -> None:
    editor = make_editor()

    result = editor.preview(
        template_id="beta-update",
        values={
            "headline": "Beta 2",
            "body": "Testing starts today.",
            "timing": "Today",
        },
    )

    assert result.template_id == "beta-update"
    assert result.template_version == 2
    assert "Beta 2" in result.content
    assert "Testing starts today." in result.content


def test_editor_rejects_missing_required_fields() -> None:
    editor = make_editor()

    with pytest.raises(ValueError, match="Missing required"):
        editor.preview(
            template_id="beta-update",
            values={"headline": "Beta 2"},
        )


def test_editor_creates_draft_with_template_snapshot() -> None:
    editor = make_editor()

    publication = editor.create_draft(
        publication_id="pub-22-2x-001",
        template_id="beta-update",
        title="Beta 2",
        values={
            "headline": "Beta 2",
            "body": "Testing starts today.",
        },
    )

    assert publication.status.value == "draft"
    assert publication.template_id == "beta-update"
    assert publication.template_version == 2
    assert "Testing starts today." in publication.content


def test_editor_does_not_publish_external_content() -> None:
    editor = make_editor()

    publication = editor.create_draft(
        publication_id="pub-22-2x-002",
        template_id="beta-update",
        title="Beta 2",
        values={
            "headline": "Beta 2",
            "body": "Draft only.",
        },
    )

    assert publication.status.value == "draft"
    assert publication.published_at is None
