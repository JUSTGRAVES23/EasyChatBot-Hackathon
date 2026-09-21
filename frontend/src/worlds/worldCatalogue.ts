export type WorldCatalogueEntry = {
  slug: string;
  worldId: string;
  name: string;
};

/*
 * Frontend route catalogue.
 *
 * The URL exposes the World slug only.
 * It never contains a conversation UUID.
 *
 * The backend remains authoritative for World existence,
 * ownership, language policy, and runtime execution.
 */
export const WORLD_CATALOGUE: readonly WorldCatalogueEntry[] = [
  {
    slug: "arabic",
    worldId: "arabic_world",
    name: "Arabic World",
  },
  {
    slug: "chinese",
    worldId: "chinese_world",
    name: "Chinese World",
  },
  {
    slug: "cybersecurity",
    worldId: "cybersecurity_world",
    name: "Cybersecurity World",
  },
  {
    slug: "dutch",
    worldId: "dutch_world",
    name: "Dutch World",
  },
  {
    slug: "english",
    worldId: "english_world",
    name: "English World",
  },
  {
    slug: "french",
    worldId: "french_world",
    name: "French World",
  },
  {
    slug: "german",
    worldId: "german_world",
    name: "German World",
  },
  {
    slug: "italian",
    worldId: "italian_world",
    name: "Italian World",
  },
  {
    slug: "luxembourgish",
    worldId: "luxembourgish_world",
    name: "Luxembourgish World",
  },
  {
    slug: "polish",
    worldId: "polish_world",
    name: "Polish World",
  },
  {
    slug: "portuguese",
    worldId: "portuguese_world",
    name: "Portuguese World",
  },
  {
    slug: "russian",
    worldId: "russian_world",
    name: "Russian World",
  },
  {
    slug: "spanish",
    worldId: "spanish_world",
    name: "Spanish World",
  },
];

export function getWorldBySlug(
  slug: string,
): WorldCatalogueEntry | undefined {
  const normalized = slug.trim().toLowerCase();

  return WORLD_CATALOGUE.find(
    (world) => world.slug === normalized,
  );
}