export type CreatePrivateChatResponse = {
  conversation_id: string;
  world_id: string;
};

export type PrivateChatMessageResponse = {
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

export type ActivePrivateChatConversationResponse = {
  conversation_id: string;
  world_id: string;
  messages: PrivateChatMessageResponse[];
};

export type SendPrivateChatMessageResponse = {
  conversation_id: string;
  world_id: string;
  response: string;
  response_language: string;
};

type ApiErrorPayload = {
  detail?: unknown;
};

async function parseError(
  response: Response,
  fallback: string,
): Promise<Error> {
  let detail = fallback;

  try {
    const payload = (await response.json()) as ApiErrorPayload;

    if (
      typeof payload.detail === "string" &&
      payload.detail.trim()
    ) {
      detail = payload.detail;
    }
  } catch {
    // Keep the safe fallback when the response is not JSON.
  }

  return new Error(
    `${detail} (HTTP ${response.status})`,
  );
}

/**
 * Resolve the authenticated learner's active conversation for one World.
 *
 * The World is identified by its server-owned runtime ID. The conversation
 * UUID remains an internal/server-side identifier and is never placed in
 * the public World URL.
 *
 * On first access the backend may create the initial active conversation.
 * On subsequent access the backend returns the existing active conversation
 * together with its persisted recent history.
 */
export async function getActivePrivateChatConversation(
  worldId: string,
): Promise<ActivePrivateChatConversationResponse> {
  const query = new URLSearchParams({
    world_id: worldId,
  });

  const response = await fetch(
    `/api/private-chat/conversations/active?${query.toString()}`,
    {
      method: "GET",
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
    },
  );

  if (!response.ok) {
    throw await parseError(
      response,
      "Unable to load the active private conversation.",
    );
  }

  return response.json() as Promise<
    ActivePrivateChatConversationResponse
  >;
}

/**
 * Explicitly create a new private conversation.
 *
 * This is the Restart operation. The backend changes the active
 * conversation pointer but does not erase historical conversations
 * or their messages.
 */
export async function createPrivateChatConversation(
  worldId: string,
): Promise<CreatePrivateChatResponse> {
  const response = await fetch(
    "/api/private-chat/conversations",
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        world_id: worldId,
      }),
    },
  );

  if (!response.ok) {
    throw await parseError(
      response,
      "Unable to create the private conversation.",
    );
  }

  return response.json() as Promise<CreatePrivateChatResponse>;
}

export async function sendPrivateChatMessage(
  conversationId: string,
  message: string,
): Promise<SendPrivateChatMessageResponse> {
  const response = await fetch(
    "/api/private-chat/messages",
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        message,
      }),
    },
  );

  if (!response.ok) {
    throw await parseError(
      response,
      "Unable to send the private-chat message.",
    );
  }

  return response.json() as Promise<SendPrivateChatMessageResponse>;
}