from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from cybersecurity.email.resend_email_provider import ResendEmailProvider


def _provider() -> ResendEmailProvider:
    return ResendEmailProvider(
        api_key="re_test_key",
        sender="cybersecurity@example.com",
    )


def test_build_attachments_preserves_inline_cid_and_content_type(
    tmp_path: Path,
) -> None:
    artwork = tmp_path / "easychatbot-password-reset.png"
    artwork.write_bytes(b"fake-png-content")

    result = ResendEmailProvider._build_attachments(
        [
            {
                "path": str(artwork),
                "filename": "easychatbot-password-reset.png",
                "inline": True,
                "content_id": "easychatbot-password-reset",
                "content_type": "image/png",
            }
        ]
    )

    assert result == [
        {
            "filename": "easychatbot-password-reset.png",
            "content": base64.b64encode(
                b"fake-png-content"
            ).decode("ascii"),
            "content_type": "image/png",
            "content_id": "easychatbot-password-reset",
        }
    ]


def test_build_attachments_derives_png_content_type(
    tmp_path: Path,
) -> None:
    artwork = tmp_path / "easychatbot-password-reset.png"
    artwork.write_bytes(b"fake-png-content")

    result = ResendEmailProvider._build_attachments(
        [
            {
                "path": str(artwork),
                "filename": "easychatbot-password-reset.png",
                "inline": True,
                "content_id": "easychatbot-password-reset",
            }
        ]
    )

    assert result[0]["content_type"] == "image/png"
    assert result[0]["content_id"] == "easychatbot-password-reset"


def test_inline_attachment_requires_content_id(
    tmp_path: Path,
) -> None:
    artwork = tmp_path / "image.png"
    artwork.write_bytes(b"fake-png-content")

    with pytest.raises(
        ValueError,
        match="Inline email attachments require content_id",
    ):
        ResendEmailProvider._build_attachments(
            [
                {
                    "path": str(artwork),
                    "filename": "image.png",
                    "inline": True,
                }
            ]
        )


@pytest.mark.asyncio
async def test_password_reset_uses_supplied_html_and_inline_attachment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    artwork = tmp_path / "easychatbot-password-reset.png"
    artwork.write_bytes(b"fake-png-content")

    provider = _provider()
    send_async = AsyncMock(return_value={"id": "resend-test-id"})

    monkeypatch.setattr(
        "cybersecurity.email.resend_email_provider.resend.Emails.send_async",
        send_async,
    )

    html = (
        '<img src="cid:easychatbot-password-reset" '
        'usemap="#easychatbot-password-reset-map">'
    )

    result = await provider.send(
        "Oops… got distracted? Let’s fix that 🔐",
        {
            "recipient": "user@example.com",
            "email_type": "authentication_password_reset",
            "from": "academy@example.com",
            "html": html,
            "body": "Password reset fallback.",
            "attachments": [
                {
                    "path": str(artwork),
                    "filename": "easychatbot-password-reset.png",
                    "inline": True,
                    "content_id": "easychatbot-password-reset",
                    "content_type": "image/png",
                }
            ],
        },
    )

    assert result == {
        "provider": "resend",
        "status": "accepted",
        "message_id": "resend-test-id",
    }

    send_async.assert_awaited_once()

    params = send_async.await_args.args[0]

    assert params["html"] == html
    assert params["text"] == "Password reset fallback."
    assert params["from"] == "academy@example.com"
    assert params["to"] == ["user@example.com"]

    assert params["attachments"] == [
        {
            "filename": "easychatbot-password-reset.png",
            "content": base64.b64encode(
                b"fake-png-content"
            ).decode("ascii"),
            "content_type": "image/png",
            "content_id": "easychatbot-password-reset",
        }
    ]


@pytest.mark.asyncio
async def test_password_reset_does_not_use_cybersecurity_renderer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    artwork = tmp_path / "easychatbot-password-reset.png"
    artwork.write_bytes(b"fake-png-content")

    provider = _provider()
    send_async = AsyncMock(return_value={"id": "resend-test-id"})

    monkeypatch.setattr(
        "cybersecurity.email.resend_email_provider.resend.Emails.send_async",
        send_async,
    )

    provider._build_html = lambda content: pytest.fail(  # type: ignore[method-assign]
        "Password-reset email must not use the cybersecurity renderer."
    )

    html = '<img src="cid:easychatbot-password-reset">'

    await provider.send(
        "Password reset",
        {
            "recipient": "user@example.com",
            "email_type": "authentication_password_reset",
            "from": "academy@example.com",
            "html": html,
            "body": "fallback",
            "attachments": [
                {
                    "path": str(artwork),
                    "filename": "easychatbot-password-reset.png",
                    "inline": True,
                    "content_id": "easychatbot-password-reset",
                    "content_type": "image/png",
                }
            ],
        },
    )

    params = send_async.await_args.args[0]
    assert params["html"] == html


@pytest.mark.asyncio
async def test_authentication_password_reset_requires_supplied_html(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = _provider()

    with pytest.raises(
        ValueError,
        match="authentication_password_reset requires html",
    ):
        await provider.send(
            "Password reset",
            {
                "recipient": "user@example.com",
                "email_type": "authentication_password_reset",
                "from": "academy@example.com",
            },
        )


@pytest.mark.asyncio
async def test_authentication_password_reset_requires_sender(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = _provider()

    with pytest.raises(
        ValueError,
        match="authentication_password_reset sender is required",
    ):
        await provider.send(
            "Password reset",
            {
                "recipient": "user@example.com",
                "email_type": "authentication_password_reset",
                "html": "<p>reset</p>",
            },
        )
