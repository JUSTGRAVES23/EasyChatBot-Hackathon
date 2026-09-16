import { useEffect, useMemo, useState } from "react";
import styles from "./CinemaShop.module.css";

export type ShopCategory = "all" | "services" | "trips" | "goods" | "other";

export type ShopRecommendation = {
  id: string;
  category: Exclude<ShopCategory, "all">;
  title: string;
  description: string;
  reason: string;
  externalUrl: string;
  sourceLabel: string;
  tags: string[];
};

const FALLBACK_RECOMMENDATIONS: ShopRecommendation[] = [
  {
    id: "french-market",
    category: "trips",
    title: "French Market Experience",
    description: "A relaxed cultural outing that can turn a French practice session into a real-world experience.",
    reason: "Suggested because it connects your French learning with your Cinema interests.",
    externalUrl: "https://www.google.com/search?q=French+market+experience",
    sourceLabel: "Explore externally",
    tags: ["French", "Culture", "Weekend"],
  },
  {
    id: "cinema-workshop",
    category: "services",
    title: "Screenwriting Workshop",
    description: "A workshop-style service for developing scenes, dialogue and story structure.",
    reason: "Fits a learner who enjoys creative and professional media topics.",
    externalUrl: "https://www.google.com/search?q=screenwriting+workshop",
    sourceLabel: "Explore externally",
    tags: ["Writing", "Cinema", "Learning"],
  },
  {
    id: "language-notebook",
    category: "goods",
    title: "French Vocabulary Notebook",
    description: "A simple physical notebook for collecting expressions, phrases and ideas from your Cinema sessions.",
    reason: "Useful for turning recommendations into lightweight learning habits.",
    externalUrl: "https://www.google.com/search?q=French+vocabulary+notebook",
    sourceLabel: "Explore externally",
    tags: ["French", "Study"],
  },
  {
    id: "festival-guide",
    category: "other",
    title: "Cinema Festival Guide",
    description: "Browse current festival programmes and discover something that catches your interest.",
    reason: "A low-pressure discovery option for your current media interests.",
    externalUrl: "https://www.google.com/search?q=film+festival+guide",
    sourceLabel: "Explore externally",
    tags: ["Film", "Discovery"],
  },
];

function normaliseRecommendations(payload: unknown): ShopRecommendation[] {
  if (!Array.isArray(payload)) return [];
  return payload.flatMap((item, index) => {
    if (!item || typeof item !== "object") return [];
    const value = item as Record<string, unknown>;
    const category = String(value.category ?? "other").toLowerCase();
    const safeCategory =
      category === "services" || category === "trips" || category === "goods"
        ? category
        : "other";
    const externalUrl = String(
      value.external_url ?? value.externalUrl ?? value.url ?? "",
    ).trim();
    if (!externalUrl || !/^https?:\/\//i.test(externalUrl)) return [];
    return [{
      id: String(value.id ?? `shop-${index}`),
      category: safeCategory as Exclude<ShopCategory, "all">,
      title: String(value.title ?? "Explore this recommendation"),
      description: String(value.description ?? "A recommendation selected for discovery."),
      reason: String(value.reason ?? "Suggested for your current interests."),
      externalUrl,
      sourceLabel: String(value.source_label ?? value.sourceLabel ?? "Explore externally"),
      tags: Array.isArray(value.tags) ? value.tags.map(String) : [],
    }];
  });
}

async function loadRecommendations(): Promise<ShopRecommendation[]> {
  try {
    const response = await fetch("/hackathon/flash-deal", {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) return [];
    const payload = await response.json();
    return normaliseRecommendations(payload.items ?? payload.recommendations ?? payload);
  } catch {
    return [];
  }
}

export default function CinemaShop() {
  const [category, setCategory] = useState<ShopCategory>("all");
  const [items, setItems] = useState<ShopRecommendation[]>(FALLBACK_RECOMMENDATIONS);

  useEffect(() => {
    let mounted = true;
    void loadRecommendations().then((remoteItems) => {
      if (mounted && remoteItems.length > 0) setItems(remoteItems);
    });
    return () => { mounted = false; };
  }, []);

  const filtered = useMemo(
    () => category === "all" ? items : items.filter((item) => item.category === category),
    [category, items],
  );

  return (
    <section className={styles.shopPage} aria-labelledby="cinema-shop-title">
      <header className={styles.shopHeader}>
        <div>
          <p className={styles.eyebrow}>EASYCHATBOT · DISCOVER</p>
          <h1 id="cinema-shop-title">Shop &amp; Discover</h1>
          <p className={styles.subtitle}>
            A few things that may fit your interests. Browse casually — there is no need to buy anything here.
          </p>
        </div>
      </header>

      <div className={styles.categoryBar} role="tablist" aria-label="Shop categories">
        {([
          ["all", "For you"],
          ["services", "Services"],
          ["trips", "Trips"],
          ["goods", "Goods"],
          ["other", "Other"],
        ] as const).map(([value, label]) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={category === value}
            className={category === value ? styles.categoryActive : styles.category}
            onClick={() => setCategory(value)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className={styles.discoveryNote}>
        <strong>Personalised discovery</strong>
        <span>Explore something interesting and continue on the actual website.</span>
      </div>

      <div className={styles.grid}>
        {filtered.map((item) => (
          <article className={styles.card} key={item.id}>
            <span className={styles.categoryLabel}>{item.category}</span>
            <h2>{item.title}</h2>
            <p className={styles.description}>{item.description}</p>
            <p className={styles.reason}>{item.reason}</p>
            <div className={styles.tags}>
              {item.tags.map((tag) => <span key={tag}>{tag}</span>)}
            </div>
            <a
              className={styles.exploreButton}
              href={item.externalUrl}
              target="_blank"
              rel="noopener noreferrer"
            >
              Explore website <span aria-hidden="true">↗</span>
            </a>
            <span className={styles.externalHint}>{item.sourceLabel}</span>
          </article>
        ))}
      </div>
    </section>
  );
}
