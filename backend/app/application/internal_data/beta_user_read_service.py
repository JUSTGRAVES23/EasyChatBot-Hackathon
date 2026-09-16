from __future__ import annotations

from typing import Any

from app.application.internal_data.beta_user_read_repository import (
    BetaUserReadRepository,
)


class BetaUserReadService:
    """Application service exposing the approved Beta-user read boundary.

    Security properties:
    - read-only;
    - no SQL;
    - no SQLAlchemy dependency;
    - no ORM objects returned;
    - no repository write methods exposed.
    """

    MAX_USER_ID_LENGTH = 128
    MAX_OUTPUT_STRING_LENGTH = 512

    def __init__(
        self,
        repository: BetaUserReadRepository,
    ) -> None:
        if repository is None:
            raise ValueError("repository cannot be None.")

        self._repository = repository

    async def get_beta_user(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:
        self._validate_user_id(user_id)

        user = await self._repository.get(user_id)

        if user is None:
            return None

        return self._to_safe_dto(user)

    async def get_beta_user_by_telegram_id(
        self,
        telegram_id: int,
    ) -> dict[str, Any] | None:
        self._validate_telegram_id(telegram_id)

        user = await self._repository.get_by_telegram_id(
            telegram_id
        )

        if user is None:
            return None

        return self._to_safe_dto(user)

    @classmethod
    def _validate_user_id(
        cls,
        user_id: str,
    ) -> None:
        if not isinstance(user_id, str):
            raise ValueError("user_id must be a string.")

        user_id = user_id.strip()

        if not user_id:
            raise ValueError("user_id cannot be empty.")

        if len(user_id) > cls.MAX_USER_ID_LENGTH:
            raise ValueError(
                "user_id exceeds the maximum allowed length."
            )

    @staticmethod
    def _validate_telegram_id(
        telegram_id: int,
    ) -> None:
        if isinstance(telegram_id, bool):
            raise ValueError(
                "telegram_id must be an integer."
            )

        if not isinstance(telegram_id, int):
            raise ValueError(
                "telegram_id must be an integer."
            )

        if telegram_id <= 0:
            raise ValueError(
                "telegram_id must be greater than zero."
            )

    @classmethod
    def _to_safe_dto(
        cls,
        user: Any,
    ) -> dict[str, Any]:
        """Convert the domain object to a controlled DTO.

        Do not return the domain/ORM object itself.
        """

        return {
            "user_id": cls._safe_string(
                getattr(user, "user_id", None)
            ),
            "email": cls._safe_string(
                getattr(user, "email", None)
            ),
            "email_verified": bool(
                getattr(user, "email_verified", False)
            ),
            "beta_approved": bool(
                getattr(user, "beta_approved", False)
            ),
            "telegram_id": getattr(
                user,
                "telegram_id",
                None,
            ),
            "active_world_id": cls._safe_string(
                getattr(user, "active_world_id", None)
            ),
        }

    @classmethod
    def _safe_string(
        cls,
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        value = str(value)

        if len(value) > cls.MAX_OUTPUT_STRING_LENGTH:
            return value[
                : cls.MAX_OUTPUT_STRING_LENGTH
            ]

        return value

