from __future__ import annotations


class InMemoryBetaEmailSender:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    async def send_beta_invitation(
        self,
        *,
        email: str,
        classroom_url: str,
    ) -> None:
        self.messages.append(
            {
                "email": email,
                "classroom_url": classroom_url,
            }
        )
