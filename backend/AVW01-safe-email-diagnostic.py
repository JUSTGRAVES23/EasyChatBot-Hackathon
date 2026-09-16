import asyncio
from urllib.parse import urlsplit, parse_qs

from app.application.identity.authentication_email_service import (
    AuthenticationEmailService,
)


class CaptureSender:
    def __init__(self):
        self.subject = None
        self.content = None

    async def send(self, subject, content):
        self.subject = subject
        self.content = content
        return {
            "provider": "diagnostic",
            "status": "captured",
            "message_id": None,
        }


async def main():
    sender = CaptureSender()

    service = AuthenticationEmailService(
        sender,
        frontend_base_url="http://localhost:3000",
    )

    await service.send_verification_email(
        email="diagnostic@example.com",
        username="diagnostic-user",
        verification_token="DIAGNOSTIC_TOKEN_NOT_REAL",
    )

    content = sender.content
    verification_url = content["html"]

    print("=== AVW-01 SAFE EMAIL PAYLOAD DIAGNOSTIC ===")
    print("Captured without external delivery: True")
    print("Email type:", content.get("email_type"))
    print("Recipient present:", bool(content.get("recipient")))
    print("Sender present:", bool(content.get("from")))
    print("HTML present:", bool(content.get("html")))
    print("Text body present:", bool(content.get("body")))
    print("Attachments:", len(content.get("attachments", [])))
    print("Subject present:", bool(sender.subject))

    print("Configured frontend base URL:", service._frontend_base_url)
    print("Registration sender present:", bool(service._registration_sender))

    print("HTML contains verification route:",
          "/verify-email?token=" in verification_url)

    print("Diagnostic token appears in HTML:",
          "DIAGNOSTIC_TOKEN_NOT_REAL" in verification_url)

    print("Recipient value:", content.get("recipient"))
    print("Sender value:", content.get("from"))
    print("Subject:", sender.subject)

    print("=== END DIAGNOSTIC ===")


if __name__ == "__main__":
    asyncio.run(main())
