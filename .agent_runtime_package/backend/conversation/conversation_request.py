"""
Provider-independent conversation request.

Represents the information required to generate a
character-aware conversational response.

The contract remains provider-independent. Optional
structured-output requirements are expressed as a
provider-neutral JSON schema and translated by the
selected provider adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ConversationRequest:
    """
    Immutable provider-independent conversation request.

    Attributes
    ----------
    system_instruction:
        Stable instruction defining how the character
        should behave.

    user_prompt:
        User-facing request to be answered.

    conversation_context:
        Optional contextual information.

    character_id:
        Identifier of the character producing the response.

    character_name:
        Display name of the character.

    response_schema:
        Optional provider-independent JSON schema describing
        the structured response expected from the provider.
        Providers are responsible for translating this schema
        into their native structured-output mechanism.
    """

    system_instruction: str

    user_prompt: str

    conversation_context: str | None = None

    character_id: str = ""

    character_name: str = ""

    response_schema: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate request invariants."""

        if not isinstance(
            self.system_instruction,
            str,
        ):
            raise ValueError(
                "system_instruction must be a string."
            )

        if not isinstance(
            self.user_prompt,
            str,
        ):
            raise ValueError(
                "user_prompt must be a string."
            )

        system_instruction = (
            self.system_instruction.strip()
        )

        user_prompt = (
            self.user_prompt.strip()
        )

        if not system_instruction:
            raise ValueError(
                "system_instruction cannot be empty."
            )

        if not user_prompt:
            raise ValueError(
                "user_prompt cannot be empty."
            )

        object.__setattr__(
            self,
            "system_instruction",
            system_instruction,
        )

        object.__setattr__(
            self,
            "user_prompt",
            user_prompt,
        )

        if self.conversation_context is not None:
            context = (
                self.conversation_context.strip()
            )

            if not context:
                raise ValueError(
                    "conversation_context cannot be blank."
                )

            object.__setattr__(
                self,
                "conversation_context",
                context,
            )

        if not isinstance(
            self.character_id,
            str,
        ):
            raise ValueError(
                "character_id must be a string."
            )

        if not isinstance(
            self.character_name,
            str,
        ):
            raise ValueError(
                "character_name must be a string."
            )

        if self.response_schema is not None:
            if not isinstance(
                self.response_schema,
                dict,
            ):
                raise ValueError(
                    "response_schema must be a dictionary."
                )

            if not self.response_schema:
                raise ValueError(
                    "response_schema cannot be empty."
                )

            object.__setattr__(
                self,
                "response_schema",
                dict(self.response_schema),
            )

        object.__setattr__(
            self,
            "character_id",
            self.character_id.strip(),
        )

        object.__setattr__(
            self,
            "character_name",
            self.character_name.strip(),
        )

    @property
    def has_conversation_context(self) -> bool:
        """Return whether contextual information exists."""

        return bool(
            self.conversation_context
        )

    @property
    def has_response_schema(self) -> bool:
        """Return whether structured output was requested."""

        return self.response_schema is not None

    @property
    def context_length(self) -> int:
        """Return the length of the conversation context."""

        if not self.conversation_context:
            return 0

        return len(
            self.conversation_context
        )

    def summary(self) -> dict[str, str]:
        """
        Return a safe diagnostic summary.

        Prompt, context and schema content are deliberately
        excluded from the summary.
        """

        return {
            "character_id": self.character_id,
            "character_name": self.character_name,
            "has_context": str(
                self.has_conversation_context
            ),
            "has_response_schema": str(
                self.has_response_schema
            ),
            "system_instruction_length": str(
                len(self.system_instruction)
            ),
            "user_prompt_length": str(
                len(self.user_prompt)
            ),
            "context_length": str(
                self.context_length
            ),
        }
