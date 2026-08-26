from __future__ import annotations

from collections.abc import Awaitable, Callable
from os import getenv

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.application.announcement.announcement_composer import (
    AnnouncementComposer,
)
from backend.app.application.announcement.announcement_publisher import (
    ControlledAnnouncementPublisher,
    PublicationDisabledError,
)
from backend.app.application.announcement.models import AnnouncementType


class AnnouncementPublishRequest(BaseModel):
    """Administrator request for publishing a Beta announcement."""

    announcement_type: AnnouncementType
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=1800)
    footer: str | None = Field(default=None, max_length=300)


class AnnouncementPublishResponse(BaseModel):
    """Controlled publication result."""

    channel_id: str
    message_id: str
    announcement_type: str
    published_at: str


AdminAuthorizer = Callable[[], Awaitable[bool]]


async def _default_admin_authorizer() -> bool:
    """
    Fail-closed default administrator authorization.

    Production composition must inject the real administrator
    authorization mechanism.
    """
    return False


def create_announcement_router(
    *,
    publisher: ControlledAnnouncementPublisher,
    composer: AnnouncementComposer | None = None,
    admin_authorizer: AdminAuthorizer = _default_admin_authorizer,
) -> APIRouter:
    """
    Create the WS-02 administrator announcement router.

    The API layer does not:
    - talk directly to Telegram;
    - construct Telegram clients;
    - bypass AnnouncementPolicy;
    - bypass ControlledAnnouncementPublisher;
    - perform autonomous publication.
    """

    if publisher is None:
        raise ValueError("publisher cannot be None.")

    if admin_authorizer is None:
        raise ValueError("admin_authorizer cannot be None.")

    announcement_composer = composer or AnnouncementComposer()

    router = APIRouter(
        prefix="/admin/announcements",
        tags=["admin-announcements"],
    )

    async def require_admin() -> None:
        try:
            authorized = await admin_authorizer()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator authorization required.",
            ) from None

        if not authorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator authorization required.",
            )

    @router.post(
        "/publish",
        response_model=AnnouncementPublishResponse,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(require_admin)],
    )
    async def publish_announcement(
        request: AnnouncementPublishRequest,
    ) -> AnnouncementPublishResponse:
        # ---------------------------------------------------------
        # Composition / policy validation
        # ---------------------------------------------------------
        try:
            composed = announcement_composer.compose(
                announcement_type=request.announcement_type,
                title=request.title,
                body=request.body,
                footer=request.footer,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        # ---------------------------------------------------------
        # Configuration
        # ---------------------------------------------------------
        try:
            channel_id = _resolve_channel_id()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        # ---------------------------------------------------------
        # Controlled publication
        #
        # PublicationDisabledError is an expected operational state.
        # It is translated here at the HTTP boundary into 503.
        # ---------------------------------------------------------
        try:
            record = await publisher.publish(
                channel_id=channel_id,
                text=composed.rendered_text,
                announcement_type=(
                    composed.announcement.announcement_type.value
                ),
            )
        except PublicationDisabledError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Telegram announcement publishing is disabled.",
            ) from None
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        # ---------------------------------------------------------
        # Successful publication
        # ---------------------------------------------------------
        return AnnouncementPublishResponse(
            channel_id=record.channel_id,
            message_id=record.message_id,
            announcement_type=record.announcement_type,
            published_at=record.published_at.isoformat(),
        )

    return router


def _resolve_channel_id() -> str:
    """
    Resolve the Beta 1 announcement channel from configuration.

    The channel ID is deliberately not hard-coded.
    """

    channel_id = getenv(
        "BETA1_ANNOUNCEMENT_CHANNEL_ID",
    )

    if not channel_id:
        raise ValueError(
            "BETA1_ANNOUNCEMENT_CHANNEL_ID is not configured."
        )

    return channel_id


__all__ = [
    "AnnouncementPublishRequest",
    "AnnouncementPublishResponse",
    "create_announcement_router",
]
