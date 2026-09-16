from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)
from app.application.private_chat.models import (
    PrivateChatConversation,
    PrivateChatMessage,
    PrivateChatResponse,
)
from app.application.private_chat.repository import PrivateChatRepository
from app.application.uai.language.language_response_policy import (
    LanguageResponsePolicy,
)
from app.application.uai.world.world_resolver import WorldResolver


MAX_PRIVATE_CHAT_MESSAGE_LENGTH = 10_000


class PrivateChatService:
    """
    Application service for authenticated World private chat.

    Security boundaries:
    - user identity is supplied by the authenticated application layer;
    - conversation ownership is enforced by user_id + world_id;
    - World configuration is resolved server-side;
    - response language is resolved server-side;
    - client input cannot select provider, character, or response language;
    - message length is enforced before runtime execution or persistence;
    - conversation activity timestamps are persisted through the repository.
    """

    def __init__(
        self,
        *,
        repository: PrivateChatRepository,
        world_resolver: WorldResolver,
        language_response_policy: LanguageResponsePolicy,
        conversation_runtime: ConversationRuntime,
    ) -> None:
        self._repository = repository
        self._world_resolver = world_resolver
        self._language_response_policy = language_response_policy
        self._conversation_runtime = conversation_runtime

    def create_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ) -> PrivateChatConversation:
        """
        Create a new private conversation for an authenticated user.

        The World is resolved before persistence so that an invalid or
        unknown World cannot create a conversation.
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")

        if not world_id or not world_id.strip():
            raise ValueError("world_id is required")

        normalized_user_id = user_id.strip()
        normalized_world_id = world_id.strip()

        self._world_resolver.resolve(normalized_world_id)

        return self._repository.create_conversation(
            user_id=normalized_user_id,
            world_id=normalized_world_id,
        )

    async def send_message(
        self,
        *,
        user_id: str,
        world_id: str,
        conversation_id: UUID,
        message: str,
        character_instruction: str,
    ) -> PrivateChatResponse:
        """
        Process one authenticated private-chat message.

        Processing order:

        1. Validate application invariants.
        2. Resolve the canonical World.
        3. Verify conversation ownership and World isolation.
        4. Resolve response language from World policy.
        5. Execute the asynchronous conversation runtime.
        6. Persist the user message.
        7. Persist the assistant message.
        8. Persist conversation activity timestamp.
        9. Return the application response.

        Provider execution happens before message persistence so a failed
        provider/runtime call does not create a successful-looking
        assistant message.
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")

        if not world_id or not world_id.strip():
            raise ValueError("world_id is required")

        if not isinstance(message, str) or not message.strip():
            raise ValueError("message is required")

        if len(message) > MAX_PRIVATE_CHAT_MESSAGE_LENGTH:
            raise ValueError(
                "message exceeds the maximum allowed length of "
                f"{MAX_PRIVATE_CHAT_MESSAGE_LENGTH} characters"
            )

        if not character_instruction or not character_instruction.strip():
            raise ValueError("character_instruction is required")

        normalized_user_id = user_id.strip()
        normalized_world_id = world_id.strip()
        normalized_message = message.strip()
        normalized_character_instruction = character_instruction.strip()

        # Resolve the canonical World before accessing the conversation.
        world = self._world_resolver.resolve(normalized_world_id)

        # The repository enforces both ownership and World isolation.
        conversation = self._repository.get_conversation(
            conversation_id=conversation_id,
            user_id=normalized_user_id,
            world_id=normalized_world_id,
        )

        if conversation is None:
            raise ValueError("Conversation not found")

        # Response language remains an application-controlled setting.
        response_language = (
            self._language_response_policy.resolve_response_language(
                world=world,
                user_message=normalized_message,
            )
        )

        # ConversationRuntime is asynchronous because provider execution
        # is asynchronous. Never persist messages before this succeeds.
        response = await self._conversation_runtime.respond(
            character_instruction=normalized_character_instruction,
            learner_message=normalized_message,
        )

        now = datetime.now(timezone.utc)

        user_message = PrivateChatMessage(
            conversation_id=conversation_id,
            role="user",
            content=normalized_message,
            created_at=now,
        )

        assistant_message = PrivateChatMessage(
            conversation_id=conversation_id,
            role="assistant",
            content=response,
            created_at=now,
        )

        self._repository.save_message(
            conversation_id=conversation_id,
            user_id=normalized_user_id,
            world_id=normalized_world_id,
            message=user_message,
        )

        self._repository.save_message(
            conversation_id=conversation_id,
            user_id=normalized_user_id,
            world_id=normalized_world_id,
            message=assistant_message,
        )

        # Persist updated_at in the database.
        self._repository.touch_conversation(
            conversation_id=conversation_id,
            user_id=normalized_user_id,
            world_id=normalized_world_id,
        )

        updated_conversation = PrivateChatConversation(
            conversation_id=conversation.conversation_id,
            user_id=conversation.user_id,
            world_id=conversation.world_id,
            created_at=conversation.created_at,
            updated_at=now,
        )

        return PrivateChatResponse(
            conversation=updated_conversation,
            user_message=user_message,
            assistant_message=assistant_message,
            response_language=response_language,
        )