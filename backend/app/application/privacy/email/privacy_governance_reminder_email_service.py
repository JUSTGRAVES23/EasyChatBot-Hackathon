from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any, Protocol

from ..privacy_governance_case_url import (
    PrivacyGovernanceCaseURLBuilder,
)


class PrivacyGovernanceEmailSender(Protocol):
    """Adapter responsible for controlled email delivery."""

    async def send(
        self,
        *,
        recipient: str,
        subject: str,
        body: str,
        html_body: str,
        attachments: list[dict[str, Any]] | None = None,
    ) -> Any:
        ...


def _text(value: Any, default: str = "—") -> str:
    """Return a safe human-readable value."""

    if value is None:
        return default

    result = str(value).strip()

    return result if result else default


def _status_label(value: Any) -> str:
    """Convert internal status values into readable labels."""

    result = _text(value)

    return result.replace("_", " ")


def _assessment_type(case: Any) -> str:
    """Derive a human-readable assessment type from the case trigger."""

    trigger = getattr(case, "trigger", None)

    trigger_type = None

    if isinstance(trigger, dict):
        trigger_type = trigger.get("type")

    elif trigger is not None:
        trigger_type = getattr(
            trigger,
            "type",
            None,
        )

    trigger_type = _text(
        trigger_type,
        "PRIVACY_ASSESSMENT",
    ).upper()

    mapping = {
        "NEW_PROCESSING": "New data processing request",
        "DATA_MAPPING": "Data mapping assessment",
        "PROCESSOR_CHANGE": "Processor change assessment",
        "RETENTION_CHANGE": "Data retention assessment",
        "DPIA_SCREENING": "DPIA screening",
        "PRIVACY_CHANGE": "Privacy change assessment",
    }

    return mapping.get(
        trigger_type,
        "Privacy governance assessment",
    )


def _normalise_ids(
    values: Any,
) -> list[str]:
    """Return clean identifiers without inventing missing data."""

    if not values:
        return []

    if isinstance(values, str):
        values = [values]

    return [
        str(value).strip()
        for value in values
        if str(value).strip()
    ]


@dataclass(slots=True)
class PrivacyGovernanceReminderEmailService:
    """Build and deliver a concise DPO/GRC governance email.

    Authoritative source:
        PrivacyGovernanceCase

    The service creates a controlled presentation snapshot of the case.

    It does NOT:
    - create governance data;
    - query the frontend;
    - query the dashboard;
    - approve a case;
    - reject a case;
    - request changes;
    - modify governance state.
    """

    sender: PrivacyGovernanceEmailSender
    recipient: str
    case_url_builder: PrivacyGovernanceCaseURLBuilder
    logo_path: Path

    def _extract_case_data(
        self,
        case: Any,
    ) -> dict[str, Any]:
        """Extract only information supported by the authoritative case."""

        case_id = getattr(
            case,
            "case_id",
            None,
        )

        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(
                "case.case_id is required."
            )

        processing_ids = _normalise_ids(
            getattr(
                case,
                "processing_ids",
                None,
            )
        )

        data_map_ids = _normalise_ids(
            getattr(
                case,
                "data_map_ids",
                None,
            )
        )

        return {
            "case_id": case_id.strip(),
            "change_id": _text(
                getattr(case, "change_id", None),
            ),
            "title": _text(
                getattr(
                    case,
                    "title",
                    None,
                ),
                "Privacy governance assessment",
            ),
            "summary": _text(
                getattr(
                    case,
                    "summary",
                    None,
                ),
                "A privacy-impacting change requires governance review.",
            ),
            "assessment_type": _assessment_type(
                case,
            ),
            "risk": _status_label(
                getattr(
                    case,
                    "risk",
                    None,
                ),
            ),
            "validation_status": _status_label(
                getattr(
                    case,
                    "validation_status",
                    None,
                ),
            ),
            "governance_status": _status_label(
                getattr(
                    case,
                    "governance_status",
                    None,
                ),
            ),
            "processing_ids": processing_ids,
            "data_map_ids": data_map_ids,
        }

    def _render_html(
        self,
        *,
        case: Any,
        case_url: str,
    ) -> str:
        """Render the concise responsive DPO/GRC email."""

        data = self._extract_case_data(case)

        case_id = escape(data["case_id"])
        change_id = escape(data["change_id"])
        title = escape(data["title"])
        summary = escape(data["summary"])
        assessment_type = escape(
            data["assessment_type"]
        )
        risk = escape(data["risk"])
        validation = escape(
            data["validation_status"]
        )
        governance_status = escape(
            data["governance_status"]
        )
        safe_case_url = escape(
            case_url,
            quote=True,
        )

        processing_html = ""

        if data["processing_ids"]:
            values = ", ".join(
                escape(value)
                for value in data["processing_ids"]
            )

            processing_html = f"""
              <tr>
                <td style="padding:9px 0;color:#68778d;
                vertical-align:top;">
                  Affected processing
                </td>
                <td style="padding:9px 0;text-align:right;
                font-weight:600;color:#17233c;">
                  {values}
                </td>
              </tr>
            """

        data_map_html = ""

        if data["data_map_ids"]:
            values = ", ".join(
                escape(value)
                for value in data["data_map_ids"]
            )

            data_map_html = f"""
              <tr>
                <td style="padding:9px 0;color:#68778d;
                vertical-align:top;">
                  Data mapping
                </td>
                <td style="padding:9px 0;text-align:right;
                font-weight:600;color:#17233c;">
                  {values}
                </td>
              </tr>
            """

        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta
    name="viewport"
    content="width=device-width,initial-scale=1"
  >
  <title>EasyChatBot Privacy Governance Review</title>
</head>

<body style="
  margin:0;
  padding:0;
  background:#f4f7fb;
  font-family:Arial,Helvetica,sans-serif;
  color:#17233c;
">

<table
  role="presentation"
  width="100%"
  cellspacing="0"
  cellpadding="0"
  border="0"
  style="background:#f4f7fb;"
>
<tr>
<td align="center" style="padding:24px 12px;">

<table
  role="presentation"
  width="100%"
  cellspacing="0"
  cellpadding="0"
  border="0"
  style="
    max-width:680px;
    background:#ffffff;
    border:1px solid #dfe5ee;
    border-radius:16px;
    overflow:hidden;
  "
>

<!-- HEADER -->

<tr>
<td style="padding:28px 30px 18px;">

  <img
    src="cid:easychatbot-governance-logo"
    alt="EasyChatBot"
    width="120"
    style="
      display:block;
      width:120px;
      max-width:40%;
      height:auto;
      border:0;
    "
  >

  <div style="
    margin-top:18px;
    font-size:12px;
    letter-spacing:1.7px;
    font-weight:700;
    color:#183b73;
  ">
    EASYCHATBOT · PRIVACY GOVERNANCE
  </div>

</td>
</tr>

<!-- ACTION BANNER -->

<tr>
<td style="padding:0 30px 22px;">

  <div style="
    background:#fff4e5;
    border:1px solid #f2d4a3;
    border-radius:10px;
    padding:12px 15px;
    color:#8a5600;
    font-size:13px;
    font-weight:700;
    letter-spacing:.4px;
  ">
    ACTION REQUIRED — DPO/GRC REVIEW
  </div>

</td>
</tr>

<!-- INTRO -->

<tr>
<td style="padding:0 30px 24px;">

  <h1 style="
    margin:0 0 12px;
    font-size:28px;
    line-height:1.25;
    color:#17233c;
  ">
    Privacy Governance Review
  </h1>

  <p style="
    margin:0;
    font-size:16px;
    line-height:1.65;
    color:#52627a;
  ">
    A privacy-impacting change has passed automated
    privacy validation and requires explicit human
    governance review before it may proceed.
  </p>

</td>
</tr>

<!-- ASSESSMENT -->

<tr>
<td style="padding:0 30px 24px;">

  <div style="
    font-size:12px;
    letter-spacing:1.3px;
    font-weight:700;
    color:#68778d;
    margin-bottom:10px;
  ">
    ASSESSMENT
  </div>

  <table
    role="presentation"
    width="100%"
    cellspacing="0"
    cellpadding="0"
    border="0"
    style="
      border-collapse:collapse;
      background:#f7f9fc;
      border:1px solid #e1e7f0;
      border-radius:10px;
    "
  >

    <tr>
      <td style="
        padding:11px 14px;
        color:#68778d;
        width:42%;
      ">
        Assessment type
      </td>

      <td style="
        padding:11px 14px;
        text-align:right;
        font-weight:600;
        color:#17233c;
      ">
        {assessment_type}
      </td>
    </tr>

    <tr>
      <td style="
        padding:11px 14px;
        color:#68778d;
      ">
        Case ID
      </td>

      <td style="
        padding:11px 14px;
        text-align:right;
        font-weight:700;
        color:#17233c;
      ">
        {case_id}
      </td>
    </tr>

    <tr>
      <td style="
        padding:11px 14px;
        color:#68778d;
      ">
        Change ID
      </td>

      <td style="
        padding:11px 14px;
        text-align:right;
        font-weight:600;
        color:#17233c;
      ">
        {change_id}
      </td>
    </tr>

    <tr>
      <td style="
        padding:11px 14px;
        color:#68778d;
      ">
        Title
      </td>

      <td style="
        padding:11px 14px;
        text-align:right;
        font-weight:600;
        color:#17233c;
      ">
        {title}
      </td>
    </tr>

    <tr>
      <td style="
        padding:11px 14px;
        color:#68778d;
      ">
        Risk
      </td>

      <td style="
        padding:11px 14px;
        text-align:right;
        font-weight:700;
        color:#17233c;
      ">
        {risk}
      </td>
    </tr>

  </table>

</td>
</tr>

<!-- WHAT IS BEING ASSESSED -->

<tr>
<td style="padding:0 30px 24px;">

  <div style="
    font-size:12px;
    letter-spacing:1.3px;
    font-weight:700;
    color:#68778d;
    margin-bottom:10px;
  ">
    WHAT IS BEING ASSESSED?
  </div>

  <p style="
    margin:0;
    font-size:15px;
    line-height:1.65;
    color:#52627a;
  ">
    {summary}
  </p>

</td>
</tr>

<!-- PRIVACY SCOPE -->

<tr>
<td style="padding:0 30px 24px;">

  <div style="
    font-size:12px;
    letter-spacing:1.3px;
    font-weight:700;
    color:#68778d;
    margin-bottom:10px;
  ">
    PRIVACY SCOPE
  </div>

  <table
    role="presentation"
    width="100%"
    cellspacing="0"
    cellpadding="0"
    border="0"
    style="border-collapse:collapse;"
  >

    {processing_html}
    {data_map_html}

    <tr>
      <td style="
        padding:9px 0;
        color:#68778d;
      ">
        Automated validation
      </td>

      <td style="
        padding:9px 0;
        text-align:right;
        font-weight:700;
        color:#17233c;
      ">
        {validation}
      </td>
    </tr>

  </table>

</td>
</tr>

<!-- GOVERNANCE -->

<tr>
<td style="padding:0 30px 26px;">

  <div style="
    font-size:12px;
    letter-spacing:1.3px;
    font-weight:700;
    color:#68778d;
    margin-bottom:10px;
  ">
    GOVERNANCE
  </div>

  <div style="
    background:#f7f9fc;
    border:1px solid #e1e7f0;
    border-radius:10px;
    padding:16px;
  ">

    <div style="
      font-size:14px;
      line-height:1.7;
      color:#52627a;
    ">
      <strong style="color:#17233c;">
        Required reviewers:
      </strong>
      DPO, GRC
    </div>

    <div style="
      font-size:14px;
      line-height:1.7;
      color:#52627a;
    ">
      <strong style="color:#17233c;">
        Current status:
      </strong>
      {governance_status}
    </div>

  </div>

</td>
</tr>

<!-- CTA -->

<tr>
<td align="center" style="padding:0 30px 30px;">

  <a
    href="{safe_case_url}"
    style="
      display:inline-block;
      background:#183b73;
      color:#ffffff;
      text-decoration:none;
      font-size:15px;
      font-weight:700;
      padding:15px 30px;
      border-radius:9px;
    "
  >
    REVIEW THIS CASE
  </a>

  <p style="
    margin:14px 0 0;
    font-size:12px;
    line-height:1.5;
    color:#8793a5;
  ">
    Review the complete assessment and record the
    applicable governance decision.
  </p>

</td>
</tr>

<!-- GOVERNANCE CONTROL -->

<tr>
<td style="
  padding:22px 30px;
  background:#fbfcfe;
  border-top:1px solid #e5e9f0;
">

  <div style="
    font-size:12px;
    letter-spacing:1px;
    font-weight:700;
    color:#52627a;
    margin-bottom:8px;
  ">
    IMPORTANT GOVERNANCE CONTROL
  </div>

  <p style="
    margin:0;
    font-size:12px;
    line-height:1.65;
    color:#68778d;
  ">
    This notification is an escalation and approval request
    only. It does not itself constitute DPO or GRC approval.
    The governance decision must be explicitly recorded in
    the controlled governance system.
  </p>

</td>
</tr>

<!-- FOOTER -->

<tr>
<td align="center" style="padding:24px 24px 30px;">

  <div style="
    font-size:13px;
    font-weight:700;
    color:#183b73;
  ">
    EasyChatBot Privacy &amp; Governance
  </div>

  <div style="
    max-width:480px;
    margin:8px auto 0;
    font-size:11px;
    line-height:1.6;
    color:#8793a5;
  ">
    Automated validation provides decision-support evidence.
    It does not replace DPO, GRC, Legal, or other authorised
    human judgement.
  </div>

</td>
</tr>

</table>

</td>
</tr>
</table>

</body>
</html>
"""

    def _render_text(
        self,
        *,
        case: Any,
        case_url: str,
    ) -> str:
        """Render the plain-text fallback."""

        data = self._extract_case_data(case)

        lines = [
            "EASYCHATBOT · PRIVACY GOVERNANCE",
            "",
            "ACTION REQUIRED — DPO/GRC REVIEW",
            "",
            "A privacy-impacting change has passed automated "
            "privacy validation and requires explicit human "
            "governance review before it may proceed.",
            "",
            "ASSESSMENT",
            f"Assessment type: {data['assessment_type']}",
            f"Case ID: {data['case_id']}",
            f"Change ID: {data['change_id']}",
            f"Title: {data['title']}",
            f"Risk: {data['risk']}",
            "",
            "WHAT IS BEING ASSESSED?",
            data["summary"],
            "",
            "PRIVACY SCOPE",
        ]

        if data["processing_ids"]:
            lines.append(
                "Affected processing: "
                + ", ".join(
                    data["processing_ids"]
                )
            )

        if data["data_map_ids"]:
            lines.append(
                "Data mapping: "
                + ", ".join(
                    data["data_map_ids"]
                )
            )

        lines.extend(
            [
                f"Automated validation: "
                f"{data['validation_status']}",
                "",
                "GOVERNANCE",
                "Required reviewers: DPO, GRC",
                f"Current status: "
                f"{data['governance_status']}",
                "",
                "REVIEW THIS CASE",
                case_url,
                "",
                "IMPORTANT GOVERNANCE CONTROL",
                "This notification is an escalation and approval "
                "request only. It does not itself constitute DPO "
                "or GRC approval. The governance decision must be "
                "explicitly recorded in the controlled governance "
                "system.",
                "",
                "EasyChatBot Privacy & Governance",
                "Automated validation provides decision-support "
                "evidence. It does not replace DPO, GRC, Legal, "
                "or other authorised human judgement.",
            ]
        )

        return "\n".join(lines)

    async def send_governance_reminder(
        self,
        *,
        case: Any,
        recipient_role: str = "DPO/GRC",
        reason: str = "pending_case_reminder",
    ) -> dict[str, object]:
        """Build and send one controlled governance email."""

        del recipient_role
        del reason

        if self.sender is None:
            raise ValueError(
                "sender cannot be None."
            )

        if not isinstance(self.recipient, str):
            raise ValueError(
                "recipient is required."
            )

        if not self.recipient.strip():
            raise ValueError(
                "recipient is required."
            )

        if self.case_url_builder is None:
            raise ValueError(
                "case_url_builder cannot be None."
            )

        if self.logo_path is None:
            raise ValueError(
                "logo_path cannot be None."
            )

        if not self.logo_path.exists():
            raise FileNotFoundError(
                "Governance email logo not found: "
                f"{self.logo_path}"
            )

        data = self._extract_case_data(case)

        case_id = data["case_id"]

        case_url = self.case_url_builder.build(
            case_id
        )

        subject = (
    "[EasyChatBot Privacy Governance] "
    "Approval Required — "
    f"{data['change_id']} — "
    f"{data['case_id']}"
)

        html_body = self._render_html(
            case=case,
            case_url=case_url,
        )

        text_body = self._render_text(
            case=case,
            case_url=case_url,
        )

        response = await self.sender.send(
            recipient=self.recipient.strip(),
            subject=subject,
            body=text_body,
            html_body=html_body,
            attachments=[
                {
                    "path": str(self.logo_path),
                    "filename": "easychatbot_logo.png",
                    "content_id": (
                        "easychatbot-governance-logo"
                    ),
                    "inline": True,
                }
            ],
        )

        status = "sent"
        reference: str | None = None

        if isinstance(response, dict):
            status = str(
                response.get(
                    "status",
                    "sent",
                )
            )

            value = (
                response.get("reference")
                or response.get("message_id")
            )

            if value is not None:
                reference = str(value)

        return {
            "status": status,
            "reference": reference,
            "case_url": case_url,
            "case_id": case_id,
            "change_id": data["change_id"],
        }


__all__ = [
    "PrivacyGovernanceReminderEmailService",
    "PrivacyGovernanceEmailSender",
]