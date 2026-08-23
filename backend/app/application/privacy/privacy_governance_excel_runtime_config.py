from __future__ import annotations

import os
from pathlib import Path


DEFAULT_WORKBOOK_RELATIVE_PATH = (
    Path("backend") / "data" / "privacy_governance_tracker.xlsx"
)
ENV_WORKBOOK_PATH = "EASYCHATBOT_PRIVACY_GOVERNANCE_WORKBOOK"


def get_privacy_governance_workbook_path() -> Path:
    """Resolve the Beta governance tracker path from controlled configuration.

    EASYCHATBOT_PRIVACY_GOVERNANCE_WORKBOOK may contain an absolute path or a
    path relative to the repository/application working directory.
    """

    configured = os.getenv(ENV_WORKBOOK_PATH)

    if configured and configured.strip():
        return Path(configured.strip()).expanduser()

    return DEFAULT_WORKBOOK_RELATIVE_PATH


__all__ = [
    "DEFAULT_WORKBOOK_RELATIVE_PATH",
    "ENV_WORKBOOK_PATH",
    "get_privacy_governance_workbook_path",
]
