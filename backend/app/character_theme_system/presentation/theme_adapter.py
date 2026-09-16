"""
Presentation adapter.

Keeps the existing dashboard independent from the internal theme framework.

No database access belongs here.
"""

from __future__ import annotations

from typing import Any


class DashboardThemeAdapter:
    """Convert a resolved theme into a stable dashboard payload."""

    def adapt(self, context: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(context, dict):
            raise TypeError("Dashboard theme context must be a dictionary.")

        theme = context.get("theme", {})
        if not isinstance(theme, dict):
            raise ValueError("Dashboard theme must be a dictionary.")

        return {
            "character": context.get("character", {}),
            "world": context.get("world", {}),
            "languages": context.get("languages", {}),
            "theme": theme,
            "metadata": context.get("metadata", {}),
        }
