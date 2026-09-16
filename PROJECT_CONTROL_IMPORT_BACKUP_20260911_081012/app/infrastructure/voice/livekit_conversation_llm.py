"""
LiveKit Conversation LLM Adapter.

Infrastructure adapter between LiveKit Agents
and EasyChatBot AI Runtime.

Responsibilities:
- Implement LiveKit LLM boundary.
- Translate LiveKit chat requests.
- Forward requests to ConversationRuntime.
- Convert runtime responses back to LiveKit format.

Does NOT:
- Call providers directly.
- Store conversations.
- Manage users.
- Manage LiveKit lifecycle.
- Own business logic.
"""

from __future__ import annotations


from dataclasses import dataclass


from livekit.agents import llm


from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)



@dataclass(
    frozen=True,
    slots=True,
)
class LiveKitConversationLLM(
    llm.LLM,
):
    """
    Adapter exposing EasyChatBot ConversationRuntime
    as a LiveKit Agents LLM implementation.
    """


    conversation_runtime: ConversationRuntime

    character_instruction: str



    async def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool] | None = None,
        conn_options: llm.LLMOptions | None = None,
    ) -> llm.LLMStream:
        """
        Execute a conversation request.

        LiveKit sends the conversation context.
        EasyChatBot Runtime generates the response.

        The generated response is returned through
        a LiveKit compatible stream.
        """


        messages = []


        for item in chat_ctx.items:

            if hasattr(
                item,
                "role",
            ):

                messages.append(
                    {
                        "role": item.role,
                        "content": (
                            item.content
                            if isinstance(
                                item.content,
                                str,
                            )
                            else ""
                        ),
                    }
                )



        learner_message = ""


        for message in reversed(messages):

            if (
                message["role"]
                ==
                "user"
            ):

                learner_message = (
                    message["content"]
                )

                break



        response = await (
            self.conversation_runtime.respond(
                character_instruction=(
                    self.character_instruction
                ),
                learner_message=(
                    learner_message
                ),
            )
        )


        return (
            self._create_stream(
                response,
            )
        )



    def _create_stream(
        self,
        response: str,
    ) -> llm.LLMStream:
        """
        Convert EasyChatBot response into
        a LiveKit LLMStream.
        """


        stream = (
            llm.LLMStream(
                self,
                chat_ctx=llm.ChatContext(),
            )
        )


        stream._event_queue.put_nowait(
            llm.ChatChunk(
                delta=llm.ChoiceDelta(
                    content=response,
                )
            )
        )


        stream._event_queue.put_nowait(
            None
        )


        return stream



__all__ = [
    "LiveKitConversationLLM",
]
