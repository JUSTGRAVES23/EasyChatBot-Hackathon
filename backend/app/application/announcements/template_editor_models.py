from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class TemplateEditorField:
    """UI-safe representation of one template input."""

    name: str
    required: bool
    label: str
    multiline: bool = False


@dataclass(frozen=True)
class TemplateEditorOption:
    """UI-safe approved template option."""

    template_id: str
    name: str
    category: str
    description: str
    version: int
    publication_type: str
    fields: tuple[TemplateEditorField, ...]


@dataclass(frozen=True)
class TemplateEditorPreview:
    """Preview result returned without creating or publishing a publication."""

    template_id: str
    template_version: int
    publication_type: str
    content: str


def field_label(name: str) -> str:
    """Convert a controlled field identifier into an operator-friendly label."""
    return name.replace("_", " ").strip().title()


def is_multiline_field(name: str) -> bool:
    """Keep long-form announcement fields in a textarea."""
    return name.lower() in {
        "body",
        "content",
        "summary",
        "description",
        "details",
        "message",
        "changes",
    }


def build_editor_fields(
    required_fields: frozenset[str],
    optional_fields: frozenset[str],
) -> tuple[TemplateEditorField, ...]:
    names = sorted(set(required_fields) | set(optional_fields))
    required = set(required_fields)

    return tuple(
        TemplateEditorField(
            name=name,
            required=name in required,
            label=field_label(name),
            multiline=is_multiline_field(name),
        )
        for name in names
    )
