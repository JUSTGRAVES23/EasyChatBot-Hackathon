import asyncio
from datetime import datetime, timezone

from app.application.identity.authentication_email_service import (
    _registration_email_sender,
)
from cybersecurity.email.resend_email_provider import ResendEmailProvider


async def main():
    recipient = _registration_email_sender()

    provider = ResendEmailProvider()

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    subject = "EasyChatBot Resend Delivery Test"

    text = (
        "This is a direct Resend delivery test from EasyChatBot.\n\n"
        f"Generated: {timestamp}\n\n"
        "This is NOT a password reset email."
    )

    html = f"""
    <html>
      <body>
        <h2>EasyChatBot Resend Delivery Test</h2>
        <p>This is a direct Resend delivery test from EasyChatBot.</p>
        <p><strong>Generated:</strong> {timestamp}</p>
        <p>This is <strong>NOT</strong> a password reset email.</p>
      </body>
    </html>
    """

    content = {
        "recipient": recipient,
        "email_type": "authentication_password_reset_confirmation",
        "from": recipient,
        "username": "EasyChatBot Test",
        "body": text,
        "html": html,
        "attachments": [],
    }

    print("PROVIDER =", type(provider).__name__)
    print("PROVIDER_ID =", provider.provider_id)
    print("RECIPIENT =", recipient)
    print("SUBJECT =", subject)

    try:
        result = await provider.send(subject, content)

        print()
        print("REAL_RESEND_RESULT =", result)

    except Exception as exc:
        print()
        print("REAL_RESEND_EXCEPTION =", type(exc).__name__)
        print("REAL_RESEND_EXCEPTION_MESSAGE =", str(exc))
        raise


asyncio.run(main())
