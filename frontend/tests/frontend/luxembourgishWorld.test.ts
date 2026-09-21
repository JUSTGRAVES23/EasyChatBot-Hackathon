import {
  describe,
  expect,
  it,
} from "vitest";

import {
  getWorldBySlug,
  WORLD_CATALOGUE,
} from "../../src/worlds/worldCatalogue";

describe("Luxembourgish World catalogue", () => {
  it("resolves the Luxembourgish World", () => {
    expect(
      getWorldBySlug("luxembourgish"),
    ).toEqual({
      slug: "luxembourgish",
      worldId: "luxembourgish_world",
      name: "Luxembourgish World",
    });
  });

  it("normalizes the Luxembourgish World slug", () => {
    expect(
      getWorldBySlug("  LUXEMBOURGISH  "),
    ).toEqual({
      slug: "luxembourgish",
      worldId: "luxembourgish_world",
      name: "Luxembourgish World",
    });
  });

  it("contains Luxembourgish in the canonical World catalogue", () => {
    expect(
      WORLD_CATALOGUE.some(
        (world) =>
          world.slug === "luxembourgish" &&
          world.worldId === "luxembourgish_world",
      ),
    ).toBe(true);
  });

  it("does not expose a conversation UUID in the World catalogue", () => {
    const world = getWorldBySlug("luxembourgish");

    expect(world?.worldId).toBe(
      "luxembourgish_world",
    );

    expect(world?.worldId).not.toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    );
  });
});