from __future__ import annotations

from datetime import datetime, timedelta, timezone


class TelegramPolicyMessageService:
    """
    Creates learner-facing Telegram policy messages.

    The active Learning World is the authoritative source for
    the learner-facing language.

    Responsibilities:
        - determine language from WorldContext
        - format retry/reset information
        - create localized rate-limit messages
        - create localized abuse-protection messages

    Does NOT:
        - enforce rate limits
        - enforce abuse protection
        - access Telegram
        - access persistence
        - execute AI
    """

    DEFAULT_LANGUAGE = "en"

    def rate_limit_message(
        self,
        *,
        context,
        retry_after_seconds: float | None = None,
    ) -> str:
        language = self._language_from_context(context)

        retry_text = self._format_retry(
            language=language,
            retry_after_seconds=retry_after_seconds,
        )

        messages = {
            "fr": (
                "Tu as atteint la limite de messages "
                "pour le moment. 😊 "
                f"{retry_text}"
            ),
            "es": (
                "Has alcanzado el límite de mensajes "
                "por el momento. 😊 "
                f"{retry_text}"
            ),
            "en": (
                "You have reached the classroom message "
                "limit for now. 😊 "
                f"{retry_text}"
            ),
        }

        return messages.get(
            language,
            messages[self.DEFAULT_LANGUAGE],
        )

    def abuse_limit_message(
        self,
        *,
        context,
        retry_after_seconds: float | None = None,
    ) -> str:
        language = self._language_from_context(context)

        retry_text = self._format_retry(
            language=language,
            retry_after_seconds=retry_after_seconds,
        )

        messages = {
            "fr": (
                "Tu envoies tes messages un peu trop "
                "rapidement. 😊 "
                f"{retry_text}"
            ),
            "es": (
                "Estás enviando mensajes demasiado "
                "rápido. 😊 "
                f"{retry_text}"
            ),
            "en": (
                "You are sending messages a little "
                "too quickly. 😊 "
                f"{retry_text}"
            ),
        }

        return messages.get(
            language,
            messages[self.DEFAULT_LANGUAGE],
        )

    def abuse_protection_message(
        self,
        *,
        context,
        retry_after_seconds: float | None = None,
    ) -> str:
        """
        Compatibility alias for the application boundary.

        The canonical implementation remains abuse_limit_message().
        This method keeps the policy service compatible with callers
        using the explicit 'abuse_protection' terminology.
        """

        return self.abuse_limit_message(
            context=context,
            retry_after_seconds=retry_after_seconds,
        )

    @staticmethod
    def _language_from_context(context) -> str:
        language = getattr(
            context,
            "language_code",
            None,
        )

        if not language:
            return TelegramPolicyMessageService.DEFAULT_LANGUAGE

        return str(language).strip().lower()

    @staticmethod
    def _format_retry(
        *,
        language: str,
        retry_after_seconds: float | None,
    ) -> str:
        if retry_after_seconds is None:
            return {
                "fr": "Tu pourras réessayer un peu plus tard.",
                "es": "Podrás intentarlo de nuevo un poco más tarde.",
                "en": "You can try again a little later.",
            }.get(
                language,
                "You can try again a little later.",
            )

        seconds = max(
            1,
            int(round(retry_after_seconds)),
        )

        if seconds < 60:
            return {
                "fr": (
                    f"Tu pourras réessayer dans environ "
                    f"{seconds} seconde"
                    f"{'' if seconds == 1 else 's'}."
                ),
                "es": (
                    f"Podrás intentarlo de nuevo en "
                    f"aproximadamente {seconds} segundo"
                    f"{'' if seconds == 1 else 's'}."
                ),
                "en": (
                    f"You can try again in about "
                    f"{seconds} second"
                    f"{'' if seconds == 1 else 's'}."
                ),
            }.get(
                language,
                (
                    f"You can try again in about "
                    f"{seconds} second"
                    f"{'' if seconds == 1 else 's'}."
                ),
            )

        reset_at = (
            datetime.now(timezone.utc)
            + timedelta(seconds=seconds)
        )

        reset_time = reset_at.astimezone().strftime(
            "%H:%M"
        )

        return {
            "fr": (
                f"Tu pourras reprendre ta pratique "
                f"vers {reset_time}."
            ),
            "es": (
                f"Podrás continuar tu práctica "
                f"aproximadamente a las {reset_time}."
            ),
            "en": (
                f"You can continue your classroom "
                f"practice at about {reset_time}."
            ),
        }.get(
            language,
            (
                f"You can continue your classroom "
                f"practice at about {reset_time}."
            ),
        )


__all__ = [
    "TelegramPolicyMessageService",
]