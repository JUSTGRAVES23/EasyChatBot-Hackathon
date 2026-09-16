import styles from "./ShopHomeCard.module.css";

type ShopHomeCardProps = {
  onOpenShop: () => void;
};

export default function ShopHomeCard({ onOpenShop }: ShopHomeCardProps) {
  return (
    <article className={styles.card}>
      <div className={styles.icon} aria-hidden="true">✦</div>
      <div className={styles.content}>
        <p className={styles.eyebrow}>DISCOVER</p>
        <h3>Shop &amp; Discover</h3>
        <p>
          Services, trips, goods and more — a few casual recommendations based on what interests you.
        </p>
        <button type="button" className={styles.button} onClick={onOpenShop}>
          Explore Shop <span aria-hidden="true">→</span>
        </button>
      </div>
    </article>
  );
}
