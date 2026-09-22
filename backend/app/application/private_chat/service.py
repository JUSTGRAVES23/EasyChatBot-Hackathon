from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
    ConversationRuntimeContext,
    ConversationTurn,
)
from app.application.private_chat.models import (
    PrivateChatActiveConversation,
    PrivateChatConversation,
    PrivateChatMessage,
    PrivateChatResponse,
)
from app.application.private_chat.repository import PrivateChatRepository
from app.application.uai.language.language_detector import LanguageDetector
from app.application.uai.language.language_response_policy import (
    LanguageResponsePolicy,
)
from app.application.uai.world.world_resolver import WorldResolver


MAX_PRIVATE_CHAT_MESSAGE_LENGTH = 10_000
MAX_ACTIVE_PRIVATE_CHAT_MESSAGES = 20


class PrivateChatService:
    """Application service for authenticated World private chat.

    The client supplies only the authenticated identity, conversation id,
    and learner message. The World is derived from the server-owned
    conversation record. Provider, model, character, and response language
    remain application-controlled.

    Active conversation state is server-owned and scoped to the authenticated
    user and World. Starting a new conversation changes only that active
    pointer; historical conversations, messages, and memory remain preserved.

    A transaction-scoped repository is supplied by the composition layer.
    The service commits successful persistence and rolls back failed
    persistence without knowing the underlying database implementation.
    """

    def __init__(
        self,
        *,
        repository: PrivateChatRepository,
        world_resolver: WorldResolver,
        language_response_policy: LanguageResponsePolicy,
        language_detector: LanguageDetector | None,
        conversation_runtime: ConversationRuntime,
        character_instruction: str,
    ) -> None:
        if not character_instruction or not character_instruction.strip():
            raise ValueError("character_instruction is required")

        self._repository = repository
        self._world_resolver = world_resolver
        self._language_response_policy = language_response_policy
        self._language_detector = language_detector
        self._conversation_runtime = conversation_runtime
        self._character_instruction = character_instruction.strip()

    def get_active_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ) -> PrivateChatActiveConversation:
        """Return the active conversation for a user/World pair.

        If the user has never opened private chat for this World, a new
        conversation is created and becomes active. Subsequent visits to the
        same World resolve to that same conversation until Restart explicitly
        creates another one.
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")

        if not world_id or not world_id.strip():
            raise ValueError("world_id is required")

        normalized_user_id = user_id.strip()
        normalized_world_id = world_id.strip()

        world = self._world_resolver.resolve(normalized_world_id)

        del world

        try:
            active_conversation = self._repository.get_active_conversation(
                user_id=normalized_user_id,
                world_id=normalized_world_id,
                limit=MAX_ACTIVE_PRIVATE_CHAT_MESSAGES,
            )

            if active_conversation is not None:
                return active_conversation

            conversation = self._repository.create_conversation(
                user_id=normalized_user_id,
                world_id=normalized_world_id,
            )

            self._repository.set_active_conversation(
                user_id=normalized_user_id,
                world_id=normalized_world_id,
                conversation_id=conversation.conversation_id,
            )

            self._repository.commit()

            return PrivateChatActiveConversation(
                conversation=conversation,
                messages=[],
            )
        except Exception:
            self._repository.rollback()
            raise

    def create_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ) -> PrivateChatConversation:
        """Create and activate a new conversation.

        This is the explicit Restart/new-conversation operation.

        The previous conversation is not deleted, its messages are not
        modified, and memory is not touched.
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")

        if not world_id or not world_id.strip():
            raise ValueError("world_id is required")

        normalized_user_id = user_id.strip()
        normalized_world_id = world_id.strip()

        self._world_resolver.resolve(normalized_world_id)

        try:
            conversation = self._repository.create_conversation(
                user_id=normalized_user_id,
                world_id=normalized_world_id,
            )

            self._repository.set_active_conversation(
                user_id=normalized_user_id,
                world_id=normalized_world_id,
                conversation_id=conversation.conversation_id,
            )

            self._repository.commit()

            return conversation
        except Exception:
            self._repository.rollback()
            raise

    async def send_message(
        self,
        *,
        user_id: str,
        conversation_id: UUID,
        message: str,
    ) -> PrivateChatResponse:
        """Process one authenticated message against its owned World."""
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")

        if not isinstance(message, str) or not message.strip():
            raise ValueError("message is required")

        if len(message) > MAX_PRIVATE_CHAT_MESSAGE_LENGTH:
            raise ValueError(
                "message exceeds the maximum allowed length of "
                f"{MAX_PRIVATE_CHAT_MESSAGE_LENGTH} characters"
            )

        normalized_user_id = user_id.strip()
        normalized_message = message.strip()

        # World is deliberately derived from the persisted conversation.
        # The client cannot choose or override the World while sending.
        conversation = self._repository.get_conversation_for_user(
            conversation_id=conversation_id,
            user_id=normalized_user_id,
        )

        if conversation is None:
            raise ValueError("Conversation not found")

        world = self._world_resolver.resolve(conversation.world_id)

        response_language = (
            self._language_response_policy.resolve_response_language(
                world=world,
                user_message=normalized_message,
                language_detector=self._language_detector,
            )
        )

        history = self._repository.get_recent_messages(
            conversation_id=conversation_id,
            user_id=normalized_user_id,
            world_id=conversation.world_id,
            limit=MAX_ACTIVE_PRIVATE_CHAT_MESSAGES,
        )

        runtime_context = ConversationRuntimeContext(
            world_id=world.world_id,
            world_name=world.name,
            language_code=world.language_code,
            world_type=world.world_type,
            learning_domain=world.learning_domain,
            response_language=response_language,
            history=tuple(
                ConversationTurn(
                    role=message.role,
                    content=message.content,
                )
                for message in history
            ),
        )

        # Runtime/provider execution happens before persistence.
        response = await self._conversation_runtime.respond(
            character_instruction=self._character_instruction,
            learner_message=normalized_message,
            context=runtime_context,
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

        try:
            self._repository.save_message(
                conversation_id=conversation_id,
                user_id=normalized_user_id,
                world_id=conversation.world_id,
                message=user_message,
            )

            self._repository.save_message(
                conversation_id=conversation_id,
                user_id=normalized_user_id,
                world_id=conversation.world_id,
                message=assistant_message,
            )

            self._repository.touch_conversation(
                conversation_id=conversation_id,
                user_id=normalized_user_id,
                world_id=conversation.world_id,
            )

            self._repository.commit()
        except Exception:
            self._repository.rollback()
            raise

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

    def close(self) -> None:
        """Release the request-scoped persistence resource."""
        self._repository.close()
