from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Protocol

from dotenv import dotenv_values


def _registration_email_sender() -> str:
    """Return the dedicated EasyChatBot registration sender."""
    repository_root = Path(__file__).resolve().parents[4]
    env_file = repository_root / ".env"

    configuration = dotenv_values(env_file)

    sender = configuration.get(
        "EASYCHATBOT_REGISTRATION_EMAIL"
    )

    if not isinstance(sender, str) or not sender.strip():
        raise RuntimeError(
            "EASYCHATBOT_REGISTRATION_EMAIL is not configured."
        )

    return sender.strip()


class AuthenticationEmailSender(Protocol):
    """Application boundary for authentication email delivery."""

    async def send(
        self,
        subject: str,
        content: dict,
    ) -> dict:
        ...


class AuthenticationEmailService:
    """Build and deliver branded EasyChatBot authentication emails."""

    LOGO_CONTENT_ID = "easychatbot-logo"
    MASCOT_CONTENT_ID = "easychatbot-mascot"
    PASSWORD_RESET_CONTENT_ID = "easychatbot-password-reset"

    def __init__(
        self,
        email_sender: AuthenticationEmailSender,
        *,
        frontend_base_url: str,
        privacy_url: str | None = None,
        logo_path: str | Path | None = None,
        password_reset_artwork_path: str | Path | None = None,
    ) -> None:
        self._registration_sender = _registration_email_sender()

        self._email_sender = email_sender
        self._frontend_base_url = frontend_base_url.rstrip("/")

        self._privacy_url = (
            privacy_url.strip()
            if isinstance(privacy_url, str) and privacy_url.strip()
            else None
        )

        if logo_path is None:
            logo_path = (
                Path(__file__).resolve().parents[2]
                / "assets"
                / "email"
                / "easychatbot-logo.png"
            )

        self._logo_path = Path(logo_path)

        if password_reset_artwork_path is None:
            password_reset_artwork_path = (
                Path(__file__).resolve().parents[2]
                / "assets"
                / "email"
                / "easychatbot-password-reset.png"
            )

        self._password_reset_artwork_path = Path(
            password_reset_artwork_path
        )

        if not self._logo_path.is_file():
            raise FileNotFoundError(
                f"EasyChatBot email logo not found: {self._logo_path}"
            )

    async def send_verification_email(
        self,
        *,
        email: str,
        username: str,
        verification_token: str,
    ) -> dict:
        """Build and send the account verification email."""
        recipient = email.strip()
        display_name = username.strip()

        verification_url = (
            f"{self._frontend_base_url}"
            f"/verify-email?token={verification_token}"
        )

        html = self._build_html(
            username=display_name,
            verification_url=verification_url,
        )

        text = self._build_text(
            username=display_name,
            verification_url=verification_url,
        )

        if not self._registration_sender:
            raise RuntimeError(
                "EASYCHATBOT_REGISTRATION_EMAIL is not configured."
            )

        return await self._email_sender.send(
            "🎓 Welcome to EasyChatBot, "
            f"@{display_name} — your journey starts here!",
            {
                "recipient": recipient,
                "email_type": "authentication_verification",
                "from": self._registration_sender,
                "username": display_name,
                "body": text,
                "html": html,
                "attachments": [
                    {
                        "path": str(self._logo_path),
                        "filename": "easychatbot-logo.png",
                        "inline": True,
                        "content_id": self.LOGO_CONTENT_ID,
                    }
                ],
            },
        )

    async def send_password_reset_email(
        self,
        *,
        email: str,
        username: str,
        reset_token: str,
    ) -> dict:
        """Build and send the EasyChatBot password-reset email.

        Password-reset messages are intentionally composed as normal
        email-safe HTML plus a plain-text fallback. The password-reset email
        does not depend on images, CID attachments, image maps, or external
        artwork.

        The raw reset token is used only to construct the one-time reset URL.
        It is not returned as a separate field and must never be logged.
        """
        recipient = email.strip()
        display_name = username.strip()

        if not recipient:
            raise ValueError("email must not be empty")

        if not reset_token:
            raise ValueError("reset_token must not be empty")

        # Reset tokens are URL-encoded before being placed in the query
        # string. HTML escaping is performed separately by the HTML builder.
        from urllib.parse import quote

        safe_token = quote(reset_token, safe="")
        reset_url = (
            f"{self._frontend_base_url}"
            f"/reset-password?token={safe_token}"
        )

        html = self._build_password_reset_html(
            username=display_name,
            reset_url=reset_url,
        )

        text = self._build_password_reset_text(
            username=display_name,
            reset_url=reset_url,
        )

        if not self._registration_sender:
            raise RuntimeError(
                "EASYCHATBOT_REGISTRATION_EMAIL is not configured."
            )

        # Password-reset emails deliberately have no attachments.
        attachments: list[dict] = []

        return await self._email_sender.send(
            "Reset your EasyChatBot password",
            {
                "recipient": recipient,
                "email_type": "authentication_password_reset",
                "from": self._registration_sender,
                "username": display_name,
                "body": text,
                "html": html,
                "attachments": attachments,
            },
        )

    def _build_password_reset_html(
        self,
        *,
        username: str,
        reset_url: str,
    ) -> str:
        """Build the responsive, email-client-safe password-reset HTML.

        The layout intentionally follows the EasyChatBot authentication
        branding: white card, soft blue background, navy typography,
        bright-blue CTA, friendly learning language, and reassuring security
        guidance.

        No images are required for the core message. This avoids broken
        inline-image rendering and large fixed-size artwork in Gmail and
        other email clients.
        """
        safe_username = escape(username.strip(), quote=True)
        safe_reset_url = escape(reset_url, quote=True)

        greeting = (
            f"Hi {safe_username}! 👋"
            if safe_username
            else "Hi there! 👋"
        )

        privacy_section = ""
        if self._privacy_url:
            safe_privacy_url = escape(
                self._privacy_url,
                quote=True,
            )
            privacy_section = f"""
                            <a
                                href="{safe_privacy_url}"
                                target="_blank"
                                rel="noopener noreferrer"
                                style="
                                    color:#1565ff;
                                    text-decoration:none;
                                "
                            >
                                Privacy
                            </a>
"""
        else:
            privacy_section = """
                            <span style="color:#8a9abb;">
                                Privacy
                            </span>
"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <meta name="color-scheme" content="light">
    <meta name="supported-color-schemes" content="light">
    <title>Reset your EasyChatBot password</title>
</head>

<body
    style="
        margin:0;
        padding:0;
        width:100%;
        background-color:#eef7ff;
        font-family:Arial,Helvetica,sans-serif;
        color:#122a72;
    "
>
    <!-- Hidden preheader shown by many email clients in the inbox preview. -->
    <div
        style="
            display:none;
            max-height:0;
            overflow:hidden;
            opacity:0;
            color:transparent;
            mso-hide:all;
        "
    >
        Reset your EasyChatBot password securely.
    </div>

    <table
        role="presentation"
        width="100%"
        cellpadding="0"
        cellspacing="0"
        border="0"
        style="
            width:100%;
            background-color:#eef7ff;
        "
    >
        <tr>
            <td
                align="center"
                style="padding:32px 16px;"
            >
                <table
                    role="presentation"
                    width="100%"
                    cellpadding="0"
                    cellspacing="0"
                    border="0"
                    style="
                        width:100%;
                        max-width:620px;
                        background-color:#ffffff;
                        border-radius:18px;
                    "
                >

                    <!-- Brand header -->
                    <tr>
                        <td
                            style="
                                padding:28px 32px 22px 32px;
                                border-bottom:1px solid #e4efff;
                            "
                        >
                            <table
                                role="presentation"
                                width="100%"
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                            >
                                <tr>
                                    <td
                                        valign="middle"
                                        style="
                                            font-size:25px;
                                            line-height:1.15;
                                            font-weight:700;
                                            color:#102b73;
                                        "
                                    >
                                        EasyChatBot

                                        <div
                                            style="
                                                margin-top:5px;
                                                font-size:14px;
                                                line-height:1.2;
                                                font-weight:400;
                                                font-style:italic;
                                                color:#1680ff;
                                            "
                                        >
                                            Growing With You.
                                        </div>
                                    </td>

                                    <td
                                        align="right"
                                        valign="middle"
                                        style="
                                            font-size:12px;
                                            line-height:1.4;
                                            color:#1565ff;
                                        "
                                    >
                                        Your AI companion<br>
                                        for lifelong learning
                                        <span
                                            style="
                                                display:inline-block;
                                                margin-left:5px;
                                                font-size:22px;
                                            "
                                        >
                                            ♥
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Security label -->
                    <tr>
                        <td
                            style="
                                padding:32px 40px 10px 40px;
                            "
                        >
                            <span
                                style="
                                    display:inline-block;
                                    padding:7px 12px;
                                    border-radius:20px;
                                    background-color:#e9f5ff;
                                    color:#1565ff;
                                    font-size:11px;
                                    line-height:1;
                                    font-weight:700;
                                    letter-spacing:.7px;
                                "
                            >
                                ACCOUNT SECURITY
                            </span>
                        </td>
                    </tr>

                    <!-- Main message -->
                    <tr>
                        <td
                            style="
                                padding:10px 40px 36px 40px;
                            "
                        >
                            <h1
                                style="
                                    margin:0 0 18px 0;
                                    font-size:34px;
                                    line-height:1.18;
                                    font-weight:700;
                                    color:#102b73;
                                "
                            >
                                Reset your password
                            </h1>

                            <p
                                style="
                                    margin:0 0 16px 0;
                                    font-size:18px;
                                    line-height:1.55;
                                    color:#173d91;
                                "
                            >
                                {greeting}
                            </p>

                            <p
                                style="
                                    margin:0 0 26px 0;
                                    font-size:16px;
                                    line-height:1.7;
                                    color:#35538f;
                                "
                            >
                                We received a request to reset the password
                                for your EasyChatBot account.
                            </p>

                            <!-- Primary CTA -->
                            <table
                                role="presentation"
                                width="100%"
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                                style="margin:0 0 28px 0;"
                            >
                                <tr>
                                    <td align="center">
                                        <a
                                            href="{safe_reset_url}"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            style="
                                                display:block;
                                                width:100%;
                                                box-sizing:border-box;
                                                padding:16px 24px;
                                                border-radius:10px;
                                                background-color:#1680ff;
                                                color:#ffffff;
                                                font-size:17px;
                                                line-height:1.3;
                                                font-weight:700;
                                                text-align:center;
                                                text-decoration:none;
                                            "
                                        >
                                            Reset password
                                            <span
                                                aria-hidden="true"
                                                style="
                                                    font-size:20px;
                                                    margin-left:6px;
                                                "
                                            >
                                                →
                                            </span>
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <!-- Expiry and security information -->
                            <table
                                role="presentation"
                                width="100%"
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                                style="
                                    width:100%;
                                    background-color:#edf7ff;
                                    border-radius:14px;
                                "
                            >
                                <tr>
                                    <td
                                        width="50%"
                                        valign="top"
                                        style="
                                            width:50%;
                                            padding:22px 20px;
                                            border-right:1px solid #c8e1ff;
                                        "
                                    >
                                        <div
                                            style="
                                                margin-bottom:9px;
                                                font-size:25px;
                                                line-height:1;
                                            "
                                        >
                                            ⏳
                                        </div>

                                        <div
                                            style="
                                                font-size:15px;
                                                line-height:1.45;
                                                font-weight:700;
                                                color:#123d91;
                                            "
                                        >
                                            This link expires after a limited period
                                        </div>

                                        <div
                                            style="
                                                margin-top:4px;
                                                font-size:14px;
                                                line-height:1.55;
                                                color:#49669d;
                                            "
                                        >
                                            It can only be used once.
                                        </div>
                                    </td>

                                    <td
                                        width="50%"
                                        valign="top"
                                        style="
                                            width:50%;
                                            padding:22px 20px;
                                        "
                                    >
                                        <div
                                            style="
                                                margin-bottom:9px;
                                                font-size:25px;
                                                line-height:1;
                                            "
                                        >
                                            🛡️
                                        </div>

                                        <div
                                            style="
                                                font-size:15px;
                                                line-height:1.45;
                                                font-weight:700;
                                                color:#123d91;
                                            "
                                        >
                                            Didn't request this?
                                        </div>

                                        <div
                                            style="
                                                margin-top:4px;
                                                font-size:14px;
                                                line-height:1.55;
                                                color:#49669d;
                                            "
                                        >
                                            You can safely ignore this email.
                                            Your password will not change unless you use the reset link.
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <!-- Accessibility / fallback guidance -->
                            <p
                                style="
                                    margin:24px 0 0 0;
                                    font-size:12px;
                                    line-height:1.6;
                                    color:#7084aa;
                                "
                            >
                                If the button does not work, please use the
                                password-reset option from the EasyChatBot
                                sign-in page.
                            </p>

                            <!-- Sign-off -->
                            <div
                                style="
                                    margin-top:30px;
                                    font-size:16px;
                                    line-height:1.5;
                                    color:#35538f;
                                "
                            >
                                See you inside,
                            </div>

                            <div
                                style="
                                    margin-top:3px;
                                    font-size:21px;
                                    line-height:1.3;
                                    font-weight:700;
                                    color:#102b73;
                                "
                            >
                                EasyChatBot
                            </div>

                            <div
                                style="
                                    margin-top:2px;
                                    font-size:17px;
                                    line-height:1.3;
                                    font-style:italic;
                                    color:#1680ff;
                                "
                            >
                                Growing With You.
                            </div>

                            <!-- Friendly brand note -->
                            <table
                                role="presentation"
                                width="100%"
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                                style="
                                    margin-top:26px;
                                    background-color:#edf7ff;
                                    border-radius:12px;
                                "
                            >
                                <tr>
                                    <td
                                        style="
                                            padding:15px 17px;
                                            font-size:13px;
                                            line-height:1.6;
                                            color:#21478e;
                                        "
                                    >
                                        <span
                                            style="
                                                margin-right:8px;
                                                font-size:22px;
                                            "
                                        >
                                            💡
                                        </span>
                                        <strong>P.S.</strong>
                                        Your new password doesn't need to be
                                        something you'll remember from 2017.
                                        Future-you will thank you.
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Brand values -->
                    <tr>
                        <td
                            style="
                                padding:0 40px 25px 40px;
                            "
                        >
                            <table
                                role="presentation"
                                width="100%"
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                                style="
                                    border-top:1px solid #b9dcff;
                                    border-bottom:1px solid #b9dcff;
                                "
                            >
                                <tr>
                                    <td
                                        width="33%"
                                        align="center"
                                        style="
                                            width:33%;
                                            padding:18px 4px;
                                            font-size:12px;
                                            line-height:1.4;
                                            color:#1565c0;
                                        "
                                    >
                                        <div
                                            style="
                                                margin-bottom:5px;
                                                font-size:22px;
                                            "
                                        >
                                            📖
                                        </div>
                                        Learn at your pace
                                    </td>

                                    <td
                                        width="33%"
                                        align="center"
                                        style="
                                            width:33%;
                                            padding:18px 4px;
                                            font-size:12px;
                                            line-height:1.4;
                                            color:#1565c0;
                                        "
                                    >
                                        <div
                                            style="
                                                margin-bottom:5px;
                                                font-size:22px;
                                            "
                                        >
                                            👥
                                        </div>
                                        Improve together
                                    </td>

                                    <td
                                        width="33%"
                                        align="center"
                                        style="
                                            width:33%;
                                            padding:18px 4px;
                                            font-size:12px;
                                            line-height:1.4;
                                            color:#1565c0;
                                        "
                                    >
                                        <div
                                            style="
                                                margin-bottom:5px;
                                                font-size:22px;
                                            "
                                        >
                                            🚀
                                        </div>
                                        Grow with confidence
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td
                            align="center"
                            style="
                                padding:0 32px 30px 32px;
                                font-size:12px;
                                line-height:1.6;
                                color:#7084aa;
                            "
                        >
{privacy_section}
                            <span style="padding:0 8px;">|</span>

                            <a
                                href="{escape(self._frontend_base_url, quote=True)}"
                                target="_blank"
                                rel="noopener noreferrer"
                                style="
                                    color:#1565ff;
                                    text-decoration:none;
                                "
                            >
                                Help
                            </a>

                            <span style="padding:0 8px;">|</span>

                            <a
                                href="mailto:support@easychatbot.com"
                                style="
                                    color:#1565ff;
                                    text-decoration:none;
                                "
                            >
                                Contact
                            </a>

                            <div
                                style="
                                    margin-top:10px;
                                    color:#8a9abb;
                                "
                            >
                                © 2025 EasyChatBot. All rights reserved.
                            </div>
                        </td>
                    </tr>

                </table>

                <!-- Security reassurance outside the card -->
                <div
                    style="
                        width:100%;
                        max-width:620px;
                        box-sizing:border-box;
                        padding:14px 20px 0 20px;
                        font-size:11px;
                        line-height:1.5;
                        color:#8192b3;
                        text-align:center;
                    "
                >
                    If you did not request this password reset, no action is
                    required. Your account remains protected.
                </div>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    def _build_password_reset_text(
        self,
        *,
        username: str,
        reset_url: str,
    ) -> str:
        """Build the plain-text fallback for password-reset emails."""

        display_name = username.strip()

        greeting = (
            f"Hi {display_name}! 👋"
            if display_name
            else "Hi there! 👋"
        )

        privacy_section = ""
        if self._privacy_url:
            privacy_section = f"""

Your privacy matters.
Learn how EasyChatBot handles and protects your personal data:
{self._privacy_url}
"""

        return f"""EasyChatBot
Growing With You.

Reset your password

{greeting}

We received a request to reset the password for your EasyChatBot account.

Reset password:
{reset_url}

This link expires after a limited period and can only be used once.

If you did not request this, you can safely ignore this email.
Your password will not change unless you use the reset link.

If the button does not work, copy and paste the reset address above into your browser.

See you inside,
EasyChatBot
Growing With You.

P.S. Your new password doesn't need to be something you'll remember from 2017.
Future-you will thank you.
{privacy_section}

Help: {self._frontend_base_url}
Contact: support@easychatbot.com

© 2025 EasyChatBot. All rights reserved.
"""

    def _build_html(
        self,
        *,
        username: str,
        verification_url: str,
    ) -> str:
        safe_username = escape(username)
        safe_verification_url = escape(
            verification_url,
            quote=True,
        )

        privacy_section = ""

        if self._privacy_url:
            safe_privacy_url = escape(
                self._privacy_url,
                quote=True,
            )

            privacy_section = f"""
                            <strong>Your privacy matters.</strong>
                            Learn how EasyChatBot handles and protects
                            your personal data:
                            <a
                                href="{safe_privacy_url}"
                                style="
                                    color:#374151;
                                    font-weight:700;
                                "
                            >
                                Data Protection &amp; Privacy
                            </a>
                            <br><br>
"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <title>Welcome to EasyChatBot</title>
</head>
<body
    style="
        margin:0;
        padding:0;
        background:#f6f7fb;
        font-family:Arial,Helvetica,sans-serif;
        color:#1f2937;
    "
>
    <table
        role="presentation"
        width="100%"
        cellspacing="0"
        cellpadding="0"
        border="0"
        style="background:#f6f7fb;"
    >
        <tr>
            <td align="center" style="padding:32px 16px;">
                <table
                    role="presentation"
                    width="100%"
                    cellspacing="0"
                    cellpadding="0"
                    border="0"
                    style="
                        max-width:620px;
                        background:#ffffff;
                        border-radius:18px;
                        overflow:hidden;
                    "
                >
                    <tr>
                        <td
                            align="center"
                            style="padding:32px 28px 18px;"
                        >
                            <img
                                src="cid:{self.LOGO_CONTENT_ID}"
                                alt="EasyChatBot — Growing With You."
                                style="
                                    display:block;
                                    max-width:260px;
                                    width:100%;
                                    height:auto;
                                    border:0;
                                "
                            />
                        </td>
                    </tr>

                    <tr>
                        <td
                            align="center"
                            style="padding:16px 36px 8px;"
                        >
                            <div
                                style="
                                    font-size:28px;
                                    font-weight:700;
                                "
                            >
                                🎓 Welcome to EasyChatBot
                            </div>

                            <div
                                style="
                                    margin-top:10px;
                                    font-size:17px;
                                    color:#6b7280;
                                "
                            >
                                Your journey starts here.
                            </div>
                        </td>
                    </tr>

                    <tr>
                        <td
                            style="
                                padding:28px 40px 10px;
                                font-size:16px;
                                line-height:1.7;
                            "
                        >
                            Hey {safe_username} 👋
                            <br><br>
                            Welcome to <strong>EasyChatBot!</strong>
                            <br><br>
                            You've just taken your first step into
                            your learning journey — and we're excited
                            to have you here.
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:12px 40px 22px;">
                            <table
                                role="presentation"
                                width="100%"
                                cellspacing="0"
                                cellpadding="0"
                                border="0"
                                style="
                                    background:#f4f7ff;
                                    border-radius:14px;
                                "
                            >
                                <tr>
                                    <td
                                        align="center"
                                        style="padding:24px 20px;"
                                    >
                                        <div
                                            style="
                                                font-size:13px;
                                                font-weight:700;
                                                text-transform:uppercase;
                                                letter-spacing:1px;
                                                color:#6b7280;
                                            "
                                        >
                                            Your EasyChatBot identity
                                        </div>

                                        <div
                                            style="
                                                margin-top:10px;
                                                font-size:25px;
                                                font-weight:700;
                                            "
                                        >
                                            @{safe_username}
                                        </div>

                                        <div
                                            style="
                                                margin-top:8px;
                                                font-size:14px;
                                                color:#6b7280;
                                            "
                                        >
                                            Your unique identity
                                            inside EasyChatBot.
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <tr>
                        <td
                            style="
                                padding:4px 40px 10px;
                                font-size:16px;
                                line-height:1.7;
                            "
                        >
                            You can use your EasyChatBot alias to
                            connect with other learners, participate
                            in activities and identify yourself across
                            the platform.
                            <br><br>
                            Think of it as your name inside the
                            EasyChatBot community.
                        </td>
                    </tr>

                    <tr>
                        <td
                            align="center"
                            style="padding:24px 40px 10px;"
                        >
                            <div
                                style="
                                    font-size:21px;
                                    font-weight:700;
                                "
                            >
                                🔐 One last step
                            </div>

                            <div
                                style="
                                    margin-top:10px;
                                    font-size:15px;
                                    line-height:1.6;
                                    color:#6b7280;
                                "
                            >
                                Before you enter the Academy,
                                let's make sure this email address
                                really belongs to you.
                            </div>
                        </td>
                    </tr>

                    <tr>
                        <td
                            align="center"
                            style="padding:22px 40px 28px;"
                        >
                            <a
                                href="{safe_verification_url}"
                                style="
                                    display:inline-block;
                                    padding:15px 28px;
                                    border-radius:10px;
                                    background:#111827;
                                    color:#ffffff;
                                    text-decoration:none;
                                    font-size:16px;
                                    font-weight:700;
                                "
                            >
                                VERIFY MY EMAIL ✨
                            </a>

                            <div
                                style="
                                    margin-top:16px;
                                    font-size:13px;
                                    line-height:1.5;
                                    color:#6b7280;
                                "
                            >
                                This link is valid for 24 hours
                                and can only be used once.
                            </div>

                            <div
                                style="
                                    margin-top:18px;
                                    padding:14px;
                                    background:#f9fafb;
                                    border-radius:8px;
                                    text-align:left;
                                    word-break:break-all;
                                    font-size:12px;
                                    line-height:1.5;
                                    color:#4b5563;
                                "
                            >
                                <strong>
                                    If the button does not work:
                                </strong>
                                <br>
                                Copy and paste this address into
                                your browser:
                                <br><br>
                                {safe_verification_url}
                            </div>
                        </td>
                    </tr>

                    <tr>
                        <td
                            align="center"
                            style="
                                padding:0 40px 30px;
                                font-size:15px;
                                line-height:1.6;
                            "
                        >
                            Once you're verified,
                            you're ready to start learning.
                            <br><br>
                            <strong>Learn. Practice. Grow.</strong>
                        </td>
                    </tr>

                    <tr>
                        <td
                            style="
                                padding:24px 40px;
                                background:#f9fafb;
                                font-size:12px;
                                line-height:1.6;
                                color:#6b7280;
                            "
                        >
                            If you didn't create this account,
                            you can safely ignore this email.
                            <br><br>

                            This is an automated message from EasyChatBot.
                            <br><br>

                            {privacy_section}

                            <strong>EasyChatBot</strong><br>
                            Growing With You.
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    def _build_text(
        self,
        *,
        username: str,
        verification_url: str,
    ) -> str:
        privacy_section = ""

        if self._privacy_url:
            privacy_section = f"""
Your privacy matters.
Learn how EasyChatBot handles and protects your personal data:
{self._privacy_url}
"""

        return f"""🎓 Welcome to EasyChatBot

Your journey starts here.

Hey {username} 👋

Welcome to EasyChatBot!

You've just taken your first step into your learning journey —
and we're excited to have you here.

YOUR EASYCHATBOT IDENTITY

@{username}

Your unique identity inside EasyChatBot.

You can use your EasyChatBot alias to connect with other learners,
participate in activities and identify yourself across the platform.

Think of it as your name inside the EasyChatBot community.

ONE LAST STEP

Before you enter the Academy, let's make sure this email address
really belongs to you.

Verify your email:
{verification_url}

If the verification button does not work, copy and paste the
verification address above directly into your browser.

This link is valid for 24 hours and can only be used once.

Once you're verified, you're ready to start learning.

Learn. Practice. Grow.

If you didn't create this account, you can safely ignore this email.

This is an automated message from EasyChatBot.

{privacy_section}

EasyChatBot
Growing With You.
"""