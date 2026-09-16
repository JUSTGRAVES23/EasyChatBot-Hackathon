import { useEffect, useMemo, useState } from "react";
import styles from "./ShopPage.module.css";

type Deal = {
  deal_id?: string;
  mode?: string;
  demo?: boolean;
  character?: { id?: string; name?: string; message?: string };
  product?: { name?: string; tagline?: string; image_url?: string; highlights?: string[]; description?: string };
  pricing?: { current?: number; previous?: number; discount_percentage?: number; currency?: string; savings?: number };
  vendor?: { name?: string; url?: string };
  actions?: { get_deal_url?: string; more_information_url?: string };
  relevance_reason?: string;
  // Compatibility with an older flat demo response.
  product_name?: string;
  vendor_name?: string;
  current_price?: number;
  previous_price?: number;
  discount_percentage?: number;
  currency?: string;
  product_image_url?: string;
  relevanceReason?: string;
};

function normaliseDeal(raw: Deal) {
  return {
    id: raw.deal_id ?? "demo-deal",
    character: raw.character?.name ?? "Yeti",
    message: raw.character?.message ?? "Look what I found! This could be perfect for you.",
    product: raw.product?.name ?? raw.product_name ?? "Recommendation",
    tagline: raw.product?.tagline ?? "A personalised find.",
    image: raw.product?.image_url ?? raw.product_image_url ?? "",
    highlights: raw.product?.highlights ?? [],
    current: raw.pricing?.current ?? raw.current_price ?? null,
    previous: raw.pricing?.previous ?? raw.previous_price ?? null,
    discount: raw.pricing?.discount_percentage ?? raw.discount_percentage ?? null,
    currency: raw.pricing?.currency ?? raw.currency ?? "EUR",
    vendor: raw.vendor?.name ?? raw.vendor_name ?? "Demo Vendor",
    vendorUrl: raw.vendor?.url ?? raw.actions?.get_deal_url ?? "#",
    infoUrl: raw.actions?.more_information_url ?? raw.vendor?.url ?? "#",
    reason: raw.relevance_reason ?? raw.relevanceReason ?? "Recommended from your current preferences.",
    demo: raw.demo === true || raw.mode === "demo",
  };
}

export default function ShopPage() {
  const [deal, setDeal] = useState<ReturnType<typeof normaliseDeal> | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/hackathon/flash-deal", { signal: controller.signal })
      .then(async (response) => {
        const body = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(body.detail ?? `Recommendation request failed (${response.status})`);
        return body;
      })
      .then((body) => {
        setDeal(normaliseDeal(body));
        setStatus("ready");
      })
      .catch((cause) => {
        if (cause?.name === "AbortError") return;
        setError(cause instanceof Error ? cause.message : "Unable to load the recommendation.");
        setStatus("error");
      });
    return () => controller.abort();
  }, []);

  const price = useMemo(() => {
    if (!deal?.current) return null;
    return new Intl.NumberFormat(undefined, { style: "currency", currency: deal.currency }).format(deal.current);
  }, [deal]);

  if (status === "loading") return <section className={styles.state}>Finding something relevant…</section>;
  if (status === "error") return <section className={styles.state} role="alert"><strong>Recommendation unavailable.</strong><span>{error}</span></section>;
  if (!deal) return null;

  return (
    <section className={styles.page} aria-labelledby="shop-title">
      <div className={styles.eyebrow}>PERSONALISED DISCOVERY</div>
      <div className={styles.headingRow}>
        <div><h1 id="shop-title">Your next find</h1><p>Character-led recommendations, explained before you act.</p></div>
        {deal.demo && <span className={styles.demo}>HACKATHON DEMO</span>}
      </div>
      <article className={styles.card}>
        {deal.image && <img className={styles.image} src={deal.image} alt="" />}
        <div className={styles.body}>
          <div className={styles.character}><span className={styles.avatar}>{deal.character.slice(0, 1)}</span><div><strong>{deal.character}</strong><p>“{deal.message}”</p></div></div>
          <h2>{deal.product}</h2><p className={styles.tagline}>{deal.tagline}</p>
          {deal.highlights.length > 0 && <ul>{deal.highlights.map((item) => <li key={item}>{item}</li>)}</ul>}
          <div className={styles.reason}><strong>Why this is relevant</strong><p>{deal.reason}</p></div>
          <div className={styles.priceRow}>{price && <strong>{price}</strong>}{deal.previous && <del>{new Intl.NumberFormat(undefined, { style: "currency", currency: deal.currency }).format(deal.previous)}</del>}{deal.discount != null && <span>{deal.discount}% off</span>}</div>
          <div className={styles.actions}><a href={deal.vendorUrl} target="_blank" rel="noreferrer">View source</a><a href={deal.infoUrl} target="_blank" rel="noreferrer">More information</a></div>
          <small>Demo recommendations are illustrative; pricing and availability are not verified live offers.</small>
        </div>
      </article>
    </section>
  );
}
