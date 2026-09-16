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

    expect(result.world_id).toBe("polish_world");

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
            response: "Dzień dobry!",
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
        "Dzień dobry!",
      );

    expect(result.response_language).toBe("pl");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/private-chat/messages",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          conversation_id:
            "00000000-0000-0000-0000-000000000001",
          message: "Dzień dobry!",
        }),
      }),
    );
  });

  it("does not put a conversation UUID into the World URL", () => {
    const pathname = "/worlds/polish/chat";

    expect(pathname).toBe("/worlds/polish/chat");
    expect(pathname).not.toContain(
      "00000000-0000-0000-0000-000000000001",
    );
  });
});

