from __future__ import annotations

import os
from pathlib import Path

from .privacy_governance_excel_sync import PrivacyGovernanceExcelSync


def create_privacy_governance_excel_sync() -> PrivacyGovernanceExcelSync:
    configured = os.getenv(
        "EASYCHATBOT_GOVERNANCE_TRACKER_PATH",
        "",
    ).strip()

    if not configured:
        raise RuntimeError(
            "EASYCHATBOT_GOVERNANCE_TRACKER_PATH is required."
        )

    return PrivacyGovernanceExcelSync(
        workbook_path=Path(configured),
    )
