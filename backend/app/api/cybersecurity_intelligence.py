"""
EasyChatBot Cybersecurity Intelligence API.

HTTP boundary for Cybersecurity Intelligence.

Endpoints:

    GET
    /api/cybersecurity-center/intelligence

        Read-only cybersecurity intelligence.

    POST
    /api/cybersecurity-center/intelligence/notify

        Explicitly execute cybersecurity intelligence and
        deliver the resulting decision-support report by email.

Architecture:

GET/POST API
    ↓
CybersecurityIntelligenceService
    ↓
RuntimeEngine
    ↓
CybersecurityIntelligenceAgent
    ↓
AgentResult
    ↓
CybersecurityEmailService
    ↓
EmailProviderManager
    ↓
ResendEmailProvider

Security boundaries:

- no remediation;
- no infrastructure modification;
- no autonomous security action;
- no direct provider calls from the API;
- email notification requires explicit POST invocation;
- cybersecurity analysis continues through RuntimeEngine.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from cybersecurity.dashboard_data_source import (
    DashboardCybersecurityDataSource,
)

from cybersecurity.email.cybersecurity_email_service import (
    CybersecurityEmailService,
)

from cybersecurity.intelligence_service import (
    CybersecurityIntelligenceService,
)


router = APIRouter(
    prefix="/api/cybersecurity-center",
    tags=["cybersecurity-center"],
)


# ============================================================
# Response models
# ============================================================


class CybersecurityIntelligenceResponse(BaseModel):
    """
    API response containing the Agent 1 decision-support result.
    """

    success: bool

    agent_id: str

    data_mode: str

    posture: str

    signal_count: int

    open_signal_count: int

    critical_count: int

    high_count: int

    medium_count: int

    low_count: int

    priority_signals: list[dict[str, Any]]

    decision_note: str

    execution_id: str | None = None


class CybersecurityNotificationResponse(
    CybersecurityIntelligenceResponse
):
    """
    Intelligence result plus explicit email delivery status.
    """

    email_status: str

    delivery_status: str

    recipient: str | None = None

    provider: dict[str, Any] | None = None

    email_error: str | None = None


# ============================================================
# Shared service construction
# ============================================================


def _create_intelligence_service() -> (
    CybersecurityIntelligenceService
):
    """
    Create the cybersecurity intelligence application service.

    The API supplies the controlled DEMO data source.

    Runtime and Agent construction remain inside the
    application service boundary.
    """

    return CybersecurityIntelligenceService(
        data_source=(
            DashboardCybersecurityDataSource()
        ),
    )


# ============================================================
# Response mapping
# ============================================================


def _build_intelligence_response(
    result,
) -> CybersecurityIntelligenceResponse:
    """
    Convert AgentResult into the HTTP response contract.
    """

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=(
                result.error
                or "Cybersecurity intelligence execution failed."
            ),
        )

    output = result.output

    if not isinstance(output, dict):
        raise HTTPException(
            status_code=500,
            detail=(
                "Cybersecurity intelligence returned "
                "an invalid output."
            ),
        )

    return CybersecurityIntelligenceResponse(
        success=result.success,
        agent_id=result.agent_id,
        data_mode="DEMO",
        posture=output["posture"],
        signal_count=output["signal_count"],
        open_signal_count=output["open_signal_count"],
        critical_count=output["critical_count"],
        high_count=output["high_count"],
        medium_count=output["medium_count"],
        low_count=output["low_count"],
        priority_signals=output[
            "priority_signals"
        ],
        decision_note=output.get(
            "decision_note",
            output.get("summary", ""),
        ),
        execution_id=output.get(
            "execution_id"
        ),
    )


# ============================================================
# Read-only intelligence endpoint
# ============================================================


@router.get(
    "/intelligence",
    response_model=CybersecurityIntelligenceResponse,
)
async def get_cybersecurity_intelligence() -> (
    CybersecurityIntelligenceResponse
):
    """
    Execute Cybersecurity Intelligence Agent using
    controlled DEMO data.

    This endpoint is read-only from an operational perspective.

    It does not send email or execute remediation.
    """

    service = _create_intelligence_service()

    result = await service.analyse(
        user_id="cybersecurity-center",
        request=(
            "Assess the current cybersecurity posture and "
            "identify the highest-priority security signals "
            "requiring attention."
        ),
    )

    return _build_intelligence_response(
        result
    )


# ============================================================
# Explicit notification endpoint
# ============================================================


@router.post(
    "/intelligence/notify",
    response_model=CybersecurityNotificationResponse,
)
async def notify_cybersecurity_intelligence() -> (
    CybersecurityNotificationResponse
):
    """
    Execute cybersecurity intelligence and explicitly
    deliver the resulting decision-support report by email.

    This endpoint is intentionally POST-only because email
    delivery is an external side effect.

    No remediation is performed.
    """

    service = _create_intelligence_service()

    result = await service.analyse(
        user_id="cybersecurity-center",
        request=(
            "Assess the current cybersecurity posture and "
            "identify the highest-priority security signals "
            "requiring attention."
        ),
    )

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=(
                result.error
                or "Cybersecurity intelligence execution failed."
            ),
        )

    output = result.output

    if not isinstance(output, dict):
        raise HTTPException(
            status_code=500,
            detail=(
                "Cybersecurity intelligence returned "
                "an invalid output."
            ),
        )

    email_service = CybersecurityEmailService()

    email_content = {
        "recipient": email_service.recipient,
        "posture": output["posture"],
        "signal_count": output["signal_count"],
        "open_signal_count": output[
            "open_signal_count"
        ],
        "critical_count": output[
            "critical_count"
        ],
        "high_count": output[
            "high_count"
        ],
        "medium_count": output[
            "medium_count"
        ],
        "low_count": output[
            "low_count"
        ],
        "priority_signals": output[
            "priority_signals"
        ],
        "decision_note": output.get(
            "decision_note",
            output.get("summary", ""),
        ),
        "execution_id": output.get(
            "execution_id"
        ),
        "data_mode": "DEMO",
        "decision_support_only": True,
        "remediation_executed": False,
    }

    email_result = await email_service.send_report(
        subject=(
            "EasyChatBot Cybersecurity "
            "Intelligence Report"
        ),
        content=email_content,
    )

    delivery_status = email_result.get(
        "delivery_status",
        "unknown",
    )

    return CybersecurityNotificationResponse(
        success=result.success,
        agent_id=result.agent_id,
        data_mode="DEMO",
        posture=output["posture"],
        signal_count=output["signal_count"],
        open_signal_count=output[
            "open_signal_count"
        ],
        critical_count=output[
            "critical_count"
        ],
        high_count=output[
            "high_count"
        ],
        medium_count=output[
            "medium_count"
        ],
        low_count=output[
            "low_count"
        ],
        priority_signals=output[
            "priority_signals"
        ],
        decision_note=output.get(
            "decision_note",
            output.get("summary", ""),
        ),
        execution_id=output.get(
            "execution_id"
        ),
        email_status=email_result.get(
            "status",
            "unknown",
        ),
        delivery_status=delivery_status,
        recipient=email_result.get(
            "recipient"
        ),
        provider=email_result.get(
            "provider"
        ),
        email_error=email_result.get(
            "error"
        ),
    )
