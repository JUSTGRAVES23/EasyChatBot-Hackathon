from __future__ import annotations

import os
from pathlib import Path

from app.application.privacy.privacy_governance_composition import (
    get_privacy_governance_composition,
)
from app.application.privacy.privacy_governance_excel_sync import (
    PrivacyGovernanceExcelSync,
)


def main() -> None:
    configured = os.getenv(
        "EASYCHATBOT_GOVERNANCE_TRACKER_PATH",
        "",
    ).strip()

    if not configured:
        raise SystemExit(
            "Set EASYCHATBOT_GOVERNANCE_TRACKER_PATH before running."
        )

    composition = get_privacy_governance_composition()

    sync = PrivacyGovernanceExcelSync(
        workbook_path=Path(configured),
    )

    sync.sync_all(
        case_registry=composition.case_registry,
        approval_registry=composition.approval_registry,
    )

    print(f"Privacy governance tracker synchronized: {configured}")


if __name__ == "__main__":
    main()

