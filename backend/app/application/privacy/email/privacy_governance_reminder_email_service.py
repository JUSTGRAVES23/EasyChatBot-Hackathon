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
        in_reply_to: str | None = None,
        references: str | None = None,
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
        trigger_type = getattr(trigger, "type", None)

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


def _normalise_ids(values: Any) -> list[str]:
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
    """Build and deliver a concise DPO/GRC governance reminder email.

    The reminder is part of the same governance email conversation as the
    initial notification whenever threading metadata is supplied.

    This service does NOT:
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

        case_id = getattr(case, "case_id", None)

        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError("case.case_id is required.")

        processing_ids = _normalise_ids(
            getattr(case, "processing_ids", None)
        )

        data_map_ids = _normalise_ids(
            getattr(case, "data_map_ids", None)
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
            "assessment_type": _assessment_type(case),
            "risk": _status_label(
                getattr(case, "risk", None),
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
        """Render the concise responsive DPO/GRC reminder email."""

        data = self._extract_case_data(case)

        case_id = escape(data["case_id"])
        change_id = escape(data["change_id"])
        title = escape(data["title"])
        summary = escape(data["summary"])
        assessment_type = escape(data["assessment_type"])
        risk = escape(data["risk"])
        validation = escape(data["validation_status"])
        governance_status = escape(data["governance_status"])
        safe_case_url = escape(case_url, quote=True)

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
  <title>EasyChatBot Privacy Governance Reminder</title>
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
    REMINDER — DPO/GRC REVIEW STILL REQUIRED
  </div>

</td>
</tr>

<tr>
<td style="padding:0 30px 24px;">

  <h1 style="
    margin:0 0 12px;
    font-size:28px;
    line-height:1.25;
    color:#17233c;
  ">
    Your review is still required
  </h1>

  <p style="
    margin:0;
    font-size:16px;
    line-height:1.65;
    color:#52627a;
  ">
    This privacy governance case is still waiting for
    human review.
  </p>

</td>
</tr>

<tr>
<td style="padding:0 30px 24px;">

  <div style="
    font-size:12px;
    letter-spacing:1.3px;
    font-weight:700;
    color:#68778d;
    margin-bottom:10px;
  ">
    CASE DETAILS
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
    "
  >

    <tr>
      <td style="padding:11px 14px;color:#68778d;">
        Change ID
      </td>

      <td style="
        padding:11px 14px;
        text-align:right;
        font-weight:700;
        color:#17233c;
      ">
        {change_id}
      </td>
    </tr>

    <tr>
      <td style="padding:11px 14px;color:#68778d;">
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

    <tr>
      <td style="padding:11px 14px;color:#68778d;">
        Validation
      </td>

      <td style="
        padding:11px 14px;
        text-align:right;
        font-weight:700;
        color:#17233c;
      ">
        {validation}
      </td>
    </tr>

    <tr>
      <td style="padding:11px 14px;color:#68778d;">
        Governance status
      </td>

      <td style="
        padding:11px 14px;
        text-align:right;
        font-weight:700;
        color:#17233c;
      ">
        {governance_status}
      </td>
    </tr>

    <tr>
      <td style="padding:11px 14px;color:#68778d;">
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

  </table>

</td>
</tr>

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

  <div style="
    font-size:16px;
    font-weight:700;
    color:#17233c;
    margin-bottom:8px;
  ">
    {title}
  </div>

  <p style="
    margin:0;
    font-size:14px;
    line-height:1.65;
    color:#52627a;
  ">
    {summary}
  </p>

</td>
</tr>

<tr>
<td style="padding:0 30px 24px;">

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

  </table>

</td>
</tr>

<tr>
<td align="center" style="padding:0 30px 30px;">

  <a
    ses:no-track
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
    REVIEW THIS CASE →
  </a>

  <p style="
    margin:14px 0 0;
    font-size:12px;
    line-height:1.5;
    color:#8793a5;
  ">
    Open the Privacy Governance Center to review
    the case and record the applicable decision.
  </p>

</td>
</tr>

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
    This email is a notification and escalation mechanism only.
    It does not constitute DPO approval, GRC approval,
    rejection, or legal advice. The controlled governance
    system remains the authoritative record of the decision.
  </p>

</td>
</tr>

<tr>
<td align="center" style="padding:24px 24px 30px;">

  <div style="
    font-size:13px;
    font-weight:700;
    color:#183b73;
  ">
    EasyChatBot Privacy &amp; Governance
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
            "REMINDER — DPO/GRC REVIEW STILL REQUIRED",
            "",
            "Your review is still required.",
            "",
            "This privacy governance case is still waiting "
            "for human review.",
            "",
            "CASE DETAILS",
            f"Change ID: {data['change_id']}",
            f"Risk: {data['risk']}",
            f"Validation: {data['validation_status']}",
            f"Governance status: {data['governance_status']}",
            f"Case ID: {data['case_id']}",
            "",
            "ASSESSMENT",
            data["title"],
            data["summary"],
            "",
            "REVIEW THIS CASE",
            case_url,
            "",
            "IMPORTANT GOVERNANCE CONTROL",
            "This email is a notification and escalation "
            "mechanism only. It does not constitute DPO "
            "approval, GRC approval, rejection, or legal advice.",
            "The controlled governance system remains the "
            "authoritative record of the decision.",
            "",
            "EasyChatBot Privacy & Governance",
        ]

        return "\n".join(lines)

    async def send_governance_reminder(
        self,
        *,
        case: Any,
        recipient_role: str = "DPO/GRC",
        reason: str = "pending_case_reminder",
        in_reply_to: str | None = None,
        references: str | None = None,
    ) -> dict[str, object]:
        """Build and send one controlled governance reminder.

        ``in_reply_to`` and ``references`` are optional because the initial
        notification has no parent message. When supplied, the provider
        should send the reminder as a reply to the existing governance
        conversation.
        """

        del recipient_role
        del reason

        if self.sender is None:
            raise ValueError("sender cannot be None.")

        if not isinstance(self.recipient, str):
            raise ValueError("recipient is required.")

        if not self.recipient.strip():
            raise ValueError("recipient is required.")

        if self.case_url_builder is None:
            raise ValueError(
                "case_url_builder cannot be None."
            )

        if self.logo_path is None:
            raise ValueError("logo_path cannot be None.")

        if not self.logo_path.exists():
            raise FileNotFoundError(
                "Governance email logo not found: "
                f"{self.logo_path}"
            )

        data = self._extract_case_data(case)

        case_id = data["case_id"]

        case_url = self.case_url_builder.build(case_id)

        subject = (
            "[EasyChatBot Privacy Governance] "
            "Reminder — Decision Required for "
            f"{case_id}"
        )

        html_body = self._render_html(
            case=case,
            case_url=case_url,
        )

        text_body = self._render_text(
            case=case,
            case_url=case_url,
        )

        send_kwargs: dict[str, Any] = {
            "recipient": self.recipient.strip(),
            "subject": subject,
            "body": text_body,
            "html_body": html_body,
            "attachments": [
                {
                    "path": str(self.logo_path),
                    "filename": "easychatbot_logo.png",
                    "content_id": "easychatbot-governance-logo",
                    "inline": True,
                }
            ],
        }

        if in_reply_to:
            send_kwargs["in_reply_to"] = in_reply_to.strip()

        if references:
            send_kwargs["references"] = references.strip()

        response = await self.sender.send(**send_kwargs)

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