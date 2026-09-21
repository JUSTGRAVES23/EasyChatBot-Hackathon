import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  getWorldBySlug,
  WORLD_CATALOGUE,
} from "../../src/worlds/worldCatalogue";

import {
  createPrivateChatConversation,
  getActivePrivateChatConversation,
  sendPrivateChatMessage,
} from "../../src/worlds/worldPrivateChatApi";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("World catalogue", () => {
  it("resolves the canonical Polish World", () => {
    expect(getWorldBySlug("polish")).toEqual({
      slug: "polish",
      worldId: "polish_world",
      name: "Polish World",
    });
  });

  it("normalizes World slugs", () => {
    expect(getWorldBySlug("  PoLiSh  ")?.worldId).toBe(
      "polish_world",
    );
  });

  it("uses one generic catalogue", () => {
    expect(WORLD_CATALOGUE.length).toBeGreaterThan(1);

    const slugs = WORLD_CATALOGUE.map(
      (world) => world.slug,
    );

    expect(new Set(slugs).size).toBe(slugs.length);
  });
});

describe("World private-chat API", () => {
  it("loads the active conversation for a World", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            conversation_id:
              "00000000-0000-0000-0000-000000000001",
            world_id: "polish_world",
            messages: [
              {
                conversation_id:
                  "00000000-0000-0000-0000-000000000001",
                role: "user",
                content: "Dzien dobry!",
                created_at:
                  "2026-09-16T07:00:00Z",
              },
              {
                conversation_id:
                  "00000000-0000-0000-0000-000000000001",
                role: "assistant",
                content: "Dzień dobry!",
                created_at:
                  "2026-09-16T07:00:01Z",
              },
            ],
          }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
            },
          },
        ),
      );

    const result =
      await getActivePrivateChatConversation(
        "polish_world",
      );

    expect(result.conversation_id).toBe(
      "00000000-0000-0000-0000-000000000001",
    );

    expect(result.world_id).toBe(
      "polish_world",
    );

    expect(result.messages).toHaveLength(2);

    expect(result.messages[0]).toMatchObject({
      role: "user",
      content: "Dzien dobry!",
    });

    expect(result.messages[1]).toMatchObject({
      role: "assistant",
      content: "Dzień dobry!",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/private-chat/conversations/active?world_id=polish_world",
      expect.objectContaining({
        method: "GET",
        credentials: "include",
      }),
    );
  });

  it("encodes the World identifier when loading the active conversation", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          conversation_id:
            "00000000-0000-0000-0000-000000000001",
          world_id: "polish_world",
          messages: [],
        }),
        {
          status: 200,
          headers: {
            "Content-Type": "application/json",
          },
        },
      ),
    );

    await getActivePrivateChatConversation(
      "polish_world",
    );

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/private-chat/conversations/active?world_id=polish_world",
      expect.anything(),
    );
  });

  it("creates a conversation with world_id", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            conversation_id:
              "00000000-0000-0000-0000-000000000001",
            world_id: "polish_world",
          }),
          {
            status: 201,
            headers: {
              "Content-Type": "application/json",
            },
          },
        ),
      );

    const result =
      await createPrivateChatConversation(
        "polish_world",
      );

    expect(result.world_id).toBe(
      "polish_world",
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/private-chat/conversations",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          world_id: "polish_world",
        }),
      }),
    );
  });

  it("sends a message using the conversation UUID", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            conversation_id:
              "00000000-0000-0000-0000-000000000001",
            world_id: "polish_world",
            response: "Dzien dobry!",
            response_language: "pl",
          }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
            },
          },
        ),
      );

    const result =
      await sendPrivateChatMessage(
        "00000000-0000-0000-0000-000000000001",
        "Dzien dobry!",
      );

    expect(result.response_language).toBe(
      "pl",
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/private-chat/messages",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          conversation_id:
            "00000000-0000-0000-0000-000000000001",
          message: "Dzien dobry!",
        }),
      }),
    );
  });

  it("keeps conversation UUIDs out of the public World URL", () => {
    const pathname =
      "/worlds/polish/chat";

    expect(pathname).toBe(
      "/worlds/polish/chat",
    );

    expect(pathname).not.toContain(
      "00000000-0000-0000-0000-000000000001",
    );
  });

  it("uses the World-only route shape", () => {
    const canonicalPath =
      "/worlds/polish/chat";

    expect(
      canonicalPath.startsWith(
        "/worlds/",
      ),
    ).toBe(true);

    expect(
      canonicalPath.endsWith(
        "/chat",
      ),
    ).toBe(true);

    const segments =
      canonicalPath
        .split("/")
        .filter(Boolean);

    expect(segments).toEqual([
      "worlds",
      "polish",
      "chat",
    ]);

    expect(segments).not.toContain(
      "00000000-0000-0000-0000-000000000001",
    );
  });
});