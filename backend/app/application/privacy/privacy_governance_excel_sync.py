from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.table import Table, TableStyleInfo


CASES_SHEET = "Privacy Governance Cases"
APPROVALS_SHEET = "Approval Evidence"
DASHBOARD_SHEET = "Governance Dashboard"


CASES_TABLE = "PrivacyGovernanceCasesTable"
APPROVALS_TABLE = "PrivacyApprovalEvidenceTable"
DASHBOARD_TABLE = "PrivacyGovernanceDashboardTable"


CASE_HEADERS = (
    "Case ID",
    "Change ID",
    "Title",
    "Summary",
    "Trigger",
    "Trigger Source",
    "Risk",
    "Validation",
    "Governance Status",
    "Email Status",
    "Triggered At",
    "Final Decision",
    "Decision Time",
    "Processing IDs",
    "Data Map IDs",
)


APPROVAL_HEADERS = (
    "Approval ID",
    "Case ID",
    "Change ID",
    "Reviewer",
    "Role",
    "Decision",
    "Comment",
    "Decided At",
)


class PrivacyGovernanceExcelSync:
    """Infrastructure adapter projecting governance state to Excel.

    The privacy registries remain authoritative.

    Excel is a downstream evidence/reporting projection and cannot change
    governance state.

    Synchronization is intentionally idempotent:

        registry state
              ↓
        Excel projection
              ↓
        repeat sync
              ↓
        same workbook state

    Existing workbook sheets are preserved, while the three governance
    projection sheets are refreshed from authoritative application state.
    """

    def __init__(
        self,
        *,
        workbook_path: Path,
    ) -> None:
        if workbook_path is None:
            raise ValueError(
                "workbook_path cannot be None."
            )

        self._workbook_path = Path(
            workbook_path
        )

    @property
    def workbook_path(self) -> Path:
        """Return the configured workbook path."""

        return self._workbook_path

    def sync_all(
        self,
        *,
        case_registry: Any,
        approval_registry: Any,
    ) -> None:
        """Synchronize authoritative governance state to Excel.

        Cases are read from the case registry.

        Approval evidence is read from the approval registry for the
        authoritative cases.

        Excel never becomes a source of governance state.
        """

        if case_registry is None:
            raise ValueError(
                "case_registry cannot be None."
            )

        if approval_registry is None:
            raise ValueError(
                "approval_registry cannot be None."
            )

        cases = tuple(
            case_registry.all()
        )

        approvals = tuple(
            approval
            for case in cases
            for approval in (
                approval_registry.for_case(
                    case.case_id
                )
            )
        )

        self._write(
            cases=cases,
            approvals=approvals,
        )

    def _write(
        self,
        *,
        cases: tuple[Any, ...],
        approvals: tuple[Any, ...],
    ) -> None:
        """Write an atomic Excel projection."""

        path = self._workbook_path

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if path.exists():
            workbook = load_workbook(path)
        else:
            workbook = Workbook()

        cases_ws = self._ensure_sheet(
            workbook,
            CASES_SHEET,
        )

        approvals_ws = self._ensure_sheet(
            workbook,
            APPROVALS_SHEET,
        )

        dashboard_ws = self._ensure_sheet(
            workbook,
            DASHBOARD_SHEET,
        )

        self._replace_cases(
            cases_ws,
            cases,
        )

        self._replace_approvals(
            approvals_ws,
            approvals,
        )

        self._write_dashboard(
            dashboard_ws,
            cases,
            approvals,
        )

        with NamedTemporaryFile(
            suffix=".xlsx",
            prefix=f"{path.stem}.",
            dir=path.parent,
            delete=False,
        ) as temp:
            temp_path = Path(
                temp.name
            )

        try:
            workbook.save(
                temp_path
            )

            temp_path.replace(
                path
            )
        finally:
            temp_path.unlink(
                missing_ok=True
            )

    @staticmethod
    def _ensure_sheet(
        workbook: Workbook,
        name: str,
    ) -> Any:
        """Return an existing sheet or create it."""

        if name in workbook.sheetnames:
            return workbook[name]

        return workbook.create_sheet(
            name
        )

    def _replace_cases(
        self,
        ws: Any,
        cases: tuple[Any, ...],
    ) -> None:
        """Replace the case evidence projection."""

        self._remove_table_if_exists(
            ws,
            CASES_TABLE,
        )

        self._clear_sheet(
            ws
        )

        ws.append(
            CASE_HEADERS
        )

        for case in cases:
            ws.append(
                (
                    case.case_id,
                    str(
                        getattr(
                            case,
                            "change_id",
                            "",
                        )
                        or ""
                    ),
                    case.title,
                    case.summary,
                    _enum_value(
                        case.trigger_type
                    ),
                    case.trigger_source,
                    _enum_upper_value(
                        case.risk
                    ),
                    case.validation_status,
                    case.governance_status,
                    case.email_status,
                    _excel_datetime(
                        case.triggered_at
                    ),
                    case.final_decision,
                    _excel_datetime(
                        case.final_decision_at
                    ),
                    _join_ids(
                        case.processing_ids
                    ),
                    _join_ids(
                        case.data_map_ids
                    ),
                )
            )

        self._format_table_sheet(
            ws,
            CASES_TABLE,
        )

    def _replace_approvals(
        self,
        ws: Any,
        approvals: tuple[Any, ...],
    ) -> None:
        """Replace the approval evidence projection."""

        self._remove_table_if_exists(
            ws,
            APPROVALS_TABLE,
        )

        self._clear_sheet(
            ws
        )

        ws.append(
            APPROVAL_HEADERS
        )

        for record in approvals:
            ws.append(
                (
                    record.approval_id,
                    record.case_id,
                    record.change_id,
                    record.reviewer,
                    record.role,
                    _enum_upper_value(
                        record.decision
                    ),
                    record.comment,
                    _excel_datetime(
                        record.decided_at
                    ),
                )
            )

        self._format_table_sheet(
            ws,
            APPROVALS_TABLE,
        )

    @staticmethod
    def _write_dashboard(
        ws: Any,
        cases: tuple[Any, ...],
        approvals: tuple[Any, ...],
    ) -> None:
        """Replace the governance dashboard projection."""

        PrivacyGovernanceExcelSync._remove_table_if_exists(
            ws,
            DASHBOARD_TABLE,
        )

        PrivacyGovernanceExcelSync._clear_sheet(
            ws
        )

        pending = sum(
            case.governance_status
            == "PENDING_DPO_GRC"
            for case in cases
        )

        approved = sum(
            case.governance_status
            == "APPROVED"
            for case in cases
        )

        blocked = sum(
            case.governance_status
            == "BLOCKED"
            for case in cases
        )

        rows = (
            (
                "Metric",
                "Value",
            ),
            (
                "Total Cases",
                len(cases),
            ),
            (
                "Pending DPO/GRC",
                pending,
            ),
            (
                "Approved",
                approved,
            ),
            (
                "Blocked",
                blocked,
            ),
            (
                "Approval Records",
                len(approvals),
            ),
            (
                "Last Sync UTC",
                datetime.now(
                    timezone.utc
                )
                .replace(
                    tzinfo=None,
                    microsecond=0,
                ),
            ),
        )

        for row in rows:
            ws.append(
                row
            )

        PrivacyGovernanceExcelSync._format_table_sheet(
            ws,
            DASHBOARD_TABLE,
        )

    @staticmethod
    def _clear_sheet(
        ws: Any,
    ) -> None:
        """Clear worksheet contents while preserving the worksheet itself."""

        if ws.max_row > 0:
            ws.delete_rows(
                1,
                ws.max_row,
            )

    @staticmethod
    def _remove_table_if_exists(
        ws: Any,
        table_name: str,
    ) -> None:
        """Remove an existing table definition before rebuilding it.

        ``delete_rows()`` removes cell contents but does not remove Excel
        table metadata. Without explicitly removing the old table,
        repeated synchronization causes openpyxl to raise:

            ValueError:
            Table with name ... already exists

        Removing only the governance table being rebuilt preserves unrelated
        workbook content and tables.
        """

        if table_name in ws.tables:
            del ws.tables[
                table_name
            ]

    @staticmethod
    def _format_table_sheet(
        ws: Any,
        table_name: str,
    ) -> None:
        """Apply standard governance tracker formatting."""

        ws.freeze_panes = "A2"

        ws.auto_filter.ref = (
            ws.dimensions
        )

        for cell in ws[1]:
            cell.font = Font(
                bold=True
            )

            cell.fill = PatternFill(
                fill_type="solid",
                fgColor="D9E2F3",
            )

            cell.alignment = Alignment(
                vertical="center"
            )

        thin = Side(
            style="thin",
            color="D9D9D9",
        )

        for row in ws.iter_rows():
            for cell in row:
                cell.border = Border(
                    bottom=thin
                )

                cell.alignment = Alignment(
                    vertical="top",
                    wrap_text=True,
                )

        for column, width in {
            "A": 24,
            "B": 24,
            "C": 32,
            "D": 48,
            "E": 22,
            "F": 24,
            "G": 14,
            "H": 14,
            "I": 22,
            "J": 18,
            "K": 24,
            "L": 18,
            "M": 24,
            "N": 28,
            "O": 28,
        }.items():
            ws.column_dimensions[
                column
            ].width = width

        if ws.max_row >= 2:
            ref = (
                f"A1:"
                f"{_column_letter(ws.max_column)}"
                f"{ws.max_row}"
            )

            table = Table(
                displayName=table_name,
                ref=ref,
            )

            table.tableStyleInfo = (
                TableStyleInfo(
                    name="TableStyleMedium2",
                    showFirstColumn=False,
                    showLastColumn=False,
                    showRowStripes=True,
                    showColumnStripes=False,
                )
            )

            ws.add_table(
                table
            )

    @staticmethod
    def _enum_value(
        value: Any,
    ) -> Any:
        """Return an enum's value when applicable."""

        return getattr(
            value,
            "value",
            value,
        )

    @staticmethod
    def _enum_upper_value(
        value: Any,
    ) -> Any:
        """Return normalized uppercase enum/text evidence."""

        resolved = getattr(
            value,
            "value",
            value,
        )

        if isinstance(
            resolved,
            str,
        ):
            return resolved.upper()

        return resolved


def _enum_value(
    value: Any,
) -> Any:
    """Return an enum's underlying value."""

    return getattr(
        value,
        "value",
        value,
    )


def _enum_upper_value(
    value: Any,
) -> Any:
    """Return an enum/text value normalized for governance evidence."""

    resolved = getattr(
        value,
        "value",
        value,
    )

    if isinstance(
        resolved,
        str,
    ):
        return resolved.upper()

    return resolved


def _excel_datetime(
    value: Any,
) -> Any:
    """Convert timezone-aware datetimes to Excel-compatible values."""

    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value.replace(
            tzinfo=None
        )

    return value


def _join_ids(
    values: Any,
) -> str:
    """Serialize identifier collections for Excel."""

    return ", ".join(
        str(value)
        for value in (
            values or ()
        )
    )


def _column_letter(
    number: int,
) -> str:
    """Convert a one-based column number to an Excel column letter."""

    result = ""

    while number:
        number, remainder = divmod(
            number - 1,
            26,
        )

        result = (
            chr(65 + remainder)
            + result
        )

    return result


__all__ = [
    "PrivacyGovernanceExcelSync",
]