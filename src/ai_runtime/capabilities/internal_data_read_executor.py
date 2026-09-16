from __future__ import annotations

from src.ai_runtime.capabilities.executor import CapabilityExecutor
from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityResult,
    CapabilityType,
)


class InternalDataReadExecutor(CapabilityExecutor):
    """Runtime adapter for the governed internal-data read capability.

    This executor deliberately contains:
    - no SQL;
    - no SQLAlchemy;
    - no database session;
    - no provider SDK;
    - no write operation.

    It delegates to an application-level read service.
    """

    GET_BETA_USER = "get_beta_user"
    GET_BETA_USER_BY_TELEGRAM_ID = (
        "get_beta_user_by_telegram_id"
    )

    _ALLOWED_OPERATIONS = frozenset(
        {
            GET_BETA_USER,
            GET_BETA_USER_BY_TELEGRAM_ID,
        }
    )

    @property
    def capability(self) -> CapabilityType:
        return CapabilityType.INTERNAL_DATA_READ

    def __init__(
        self,
        beta_user_read_service,
    ) -> None:
        if beta_user_read_service is None:
            raise ValueError(
                "beta_user_read_service cannot be None."
            )

        self._service = beta_user_read_service

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        if request is None:
            raise ValueError(
                "CapabilityRequest cannot be None."
            )

        if request.capability != self.capability:
            raise ValueError(
                "CapabilityRequest capability does not match "
                "InternalDataReadExecutor."
            )

        payload = request.payload

        operation = payload.get("operation")

        if not isinstance(operation, str):
            raise ValueError(
                "operation must be a string."
            )

        operation = operation.strip()

        if operation not in self._ALLOWED_OPERATIONS:
            raise ValueError(
                f"Unsupported internal data operation: {operation!r}"
            )

        user_id_present = "user_id" in payload
        telegram_id_present = "telegram_id" in payload

        if user_id_present == telegram_id_present:
            raise ValueError(
                "Exactly one of user_id or telegram_id "
                "must be provided."
            )

        if operation == self.GET_BETA_USER:
            if not user_id_present:
                raise ValueError(
                    "get_beta_user requires user_id."
                )

            if telegram_id_present:
                raise ValueError(
                    "get_beta_user does not accept telegram_id."
                )

            output = await (
                self._service.get_beta_user(
                    payload["user_id"]
                )
            )

        else:
            if not telegram_id_present:
                raise ValueError(
                    "get_beta_user_by_telegram_id "
                    "requires telegram_id."
                )

            if user_id_present:
                raise ValueError(
                    "get_beta_user_by_telegram_id "
                    "does not accept user_id."
                )

            output = await (
                self._service.get_beta_user_by_telegram_id(
                    payload["telegram_id"]
                )
            )

        return CapabilityResult(
            request_id=request.request_id,
            capability=self.capability,
            status=CapabilityExecutionStatus.COMPLETED,
            output={
                "found": output is not None,
                "user": output,
            },
        )


