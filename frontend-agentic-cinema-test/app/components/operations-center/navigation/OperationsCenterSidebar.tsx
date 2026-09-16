import { useMemo } from "react";
import styles from "./OperationsCenterSidebar.module.css";

type NavItemDefinition = readonly [string, string, string];

const primaryItems: readonly NavItemDefinition[] = [
  ["Overview", "/operations-center", "overview"],
  ["Providers", "/operations-center/providers", "providers"],
  ["Models", "/operations-center/models", "models"],
  ["Usage & Costs", "/operations-center/usage", "usage"],
  ["Escalations", "/operations-center/escalations", "escalations"],
  ["Quality", "/operations-center/quality", "quality"],
  ["Agents", "/operations-center/agents", "agents"],
  ["Reports", "/operations-center/reports", "reports"],
  ["Settings", "/operations-center/settings", "settings"],
];

const operationsItems: readonly NavItemDefinition[] = [
  ["Functionality Health", "/operations-center/functionality-health", "health"],
  ["Email Workflows", "/operations-center/email-workflows", "email"],
];

const comingSoonItems = ["Incidents", "Audit Trail"] as const;

const icons: Record<string, string> = {
  overview: "⌂",
  providers: "◈",
  models: "◇",
  usage: "▣",
  escalations: "△",
  quality: "♡",
  agents: "♙",
  reports: "▤",
  settings: "⚙",
  health: "⌁",
  email: "✉",
};

export default function OperationsCenterSidebar() {
  const pathname = useMemo(() => window.location.pathname, []);

  return (
    <nav className={styles.nav} aria-label="AI Operations Center">
      <div className={styles.brand}>
        <div className={styles.brandMark} aria-hidden="true">✦</div>
        <div>
          <div className={styles.brandName}>EasyChatBot</div>
          <div className={styles.brandSubtitle}>AI Operations Center</div>
        </div>
      </div>

      <div className={styles.scrollArea}>
        <NavSection label="Operations">
          {primaryItems.map(([label, href, icon]) => (
            <NavItem
              key={href}
              label={label}
              href={href}
              icon={icons[icon]}
              active={pathname === href}
            />
          ))}
        </NavSection>

        <NavSection label="Operations Control">
          {operationsItems.map(([label, href, icon]) => (
            <NavItem
              key={href}
              label={label}
              href={href}
              icon={icons[icon]}
              active={pathname === href}
            />
          ))}
          {comingSoonItems.map((label) => (
            <DisabledItem key={label} label={label} />
          ))}
        </NavSection>

        <NavSection label="Admin Operations">
          <div className={styles.accessCard}>
            <span className={styles.accessDot} aria-hidden="true" />
            <div>
              <strong>Controlled access</strong>
              <span>Operational actions require authorised access.</span>
            </div>
          </div>
        </NavSection>
      </div>

      <div className={styles.sidebarFooter}>
        <div className={styles.footerAvatar}>Y</div>
        <div>
          <strong>YETI</strong>
          <span>Your Operations Companion</span>
        </div>
      </div>
    </nav>
  );
}

function NavSection({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <section className={styles.section}>
      <h2>{label}</h2>
      <div className={styles.items}>{children}</div>
    </section>
  );
}

function NavItem({
  label,
  href,
  icon,
  active,
}: {
  label: string;
  href: string;
  icon: string;
  active: boolean;
}) {
  return (
    <a
      href={href}
      aria-current={active ? "page" : undefined}
      className={`${styles.item} ${active ? styles.itemActive : ""}`}
    >
      <span className={styles.icon} aria-hidden="true">{icon}</span>
      <span>{label}</span>
    </a>
  );
}

function DisabledItem({ label }: { label: string }) {
  return (
    <div aria-disabled="true" className={`${styles.item} ${styles.itemDisabled}`}>
      <span className={styles.icon} aria-hidden="true">·</span>
      <span>{label}</span>
      <small>Soon</small>
    </div>
  );
}
