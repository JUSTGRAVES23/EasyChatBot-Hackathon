import styles from "./GovernanceOperationsCenter.module.css";

const controls = [
  {
    id: "provider",
    title: "Provider Delivery",
    status: "Healthy",
    detail: "Provider delivery controls are operating normally.",
    href: "/operations-center/providers",
    tone: "healthy",
    icon: "◉",
  },
  {
    id: "security",
    title: "Cybersecurity",
    status: "Monitoring",
    detail: "Cybersecurity monitoring remains active.",
    href: "/operations-center/cybersecurity",
    tone: "monitoring",
    icon: "▣",
  },
  {
    id: "audit",
    title: "Audit Evidence",
    status: "Current",
    detail: "Governance evidence is current and available.",
    href: "#audit",
    tone: "healthy",
    icon: "▤",
  },
  {
    id: "changes",
    title: "Changes",
    status: "None",
    detail: "No outstanding governance changes require attention.",
    href: "#timeline",
    tone: "neutral",
    icon: "↻",
  },
] as const;

export default function GovernanceOperationsCenter() {
  return (
    <div className={styles.page}>
      <header className={styles.topbar}>
        <div className={styles.breadcrumb}>
          <span>Operations Center</span>
          <span aria-hidden="true">›</span>
          <strong>Governance</strong>
        </div>
        <div className={styles.systemState}>
          <span className={styles.liveDot} />
          All systems nominal
        </div>
      </header>

      <section className={styles.hero}>
        <div className={styles.heroGlow} />
        <div className={styles.heroContent}>
          <div className={styles.eyebrow}>EASYCHATBOT OPERATIONS CENTER</div>
          <h1>AI Governance Center</h1>
          <p>
            Governance visibility, operational controls and audit evidence
            remain under authorised human control.
          </p>
          <div className={styles.heroMeta}>
            <span className={styles.normalStatus}>
              <span className={styles.statusDot} />
              Governance operating normally
            </span>
            <span className={styles.updated}>Current governance view</span>
          </div>
        </div>
        <div className={styles.heroYeti}>
          <img src="/assets/characters/yeti-governance.png" alt="YETI Governance Guardian" />
        </div>
      </section>

      <section className={styles.healthGrid}>
        <article className={styles.healthCard}>
          <div className={styles.cardHeading}>
            <div>
              <div className={styles.cardEyebrow}>GOVERNANCE HEALTH</div>
              <h2>Overall governance health</h2>
            </div>
            <span className={styles.infoBadge} title="Governance health summary">?</span>
          </div>

          <div className={styles.healthMetric}>
            <strong>96%</strong>
            <span>Current control posture</span>
          </div>

          <div
            className={styles.healthBar}
            role="progressbar"
            aria-label="Governance health"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={96}
          >
            <span />
          </div>

          <p className={styles.healthSummary}>
            All currently represented governance controls are operating normally.
          </p>

          <div className={styles.healthStats}>
            <div>
              <strong>12</strong>
              <span>Governance controls</span>
            </div>
            <div>
              <strong>0</strong>
              <span>Open issues</span>
            </div>
            <div>
              <strong>100%</strong>
              <span>Evidence current</span>
            </div>
          </div>
        </article>

        <article className={styles.statusCard}>
          <div className={styles.cardHeading}>
            <div className={styles.cardEyebrow}>CONTROL STATUS</div>
            <span className={styles.viewLabel}>Operational overview</span>
          </div>

          <div className={styles.controlList}>
            {controls.map((control) => (
              <a key={control.id} href={control.href} className={styles.controlRow}>
                <span className={`${styles.controlIcon} ${styles[control.tone]}`} aria-hidden="true">
                  {control.icon}
                </span>
                <span className={styles.controlCopy}>
                  <strong>{control.title}</strong>
                  <span>{control.detail}</span>
                </span>
                <span className={`${styles.controlStatus} ${styles[control.tone]}`}>
                  <span className={styles.statusDot} />
                  {control.status}
                </span>
                <span className={styles.chevron} aria-hidden="true">›</span>
              </a>
            ))}
          </div>
        </article>
      </section>

      <section className={styles.insightCard}>
        <div className={styles.insightImage}>
          <img src="/assets/characters/yeti-governance.png" alt="" aria-hidden="true" />
        </div>
        <div className={styles.insightContent}>
          <div className={styles.cardEyebrow}>YETI GOVERNANCE INSIGHT</div>
          <h2>Everything looks calm from a governance perspective.</h2>
          <p>
            YETI explains governance state and evidence. Human operators remain
            responsible for decisions.
          </p>
        </div>
        <div className={styles.quote}>
          <span>“</span>
          <p>Strong governance today creates more learning opportunities tomorrow.</p>
          <small>— YETI</small>
        </div>
      </section>

      <section id="audit" className={styles.activityCard}>
        <div className={styles.activityHeading}>
          <div>
            <div className={styles.cardEyebrow}>GOVERNANCE ACTIVITY</div>
            <h2>Governance Timeline</h2>
            <p>Auditable governance activity will appear here when recorded.</p>
          </div>
          <span className={styles.readOnlyBadge}>◉ Read-only visibility</span>
        </div>

        <div id="timeline" className={styles.timelineEmpty}>
          <div className={styles.timelineIcon} aria-hidden="true">▤</div>
          <div>
            <strong>No governance events detected.</strong>
            <p>There are currently no governance events requiring review.</p>
          </div>
        </div>
      </section>

      <footer className={styles.footer}>
        <span>EasyChatBot AI Operations Center</span>
        <span>Governance visibility · Human oversight · Audit evidence</span>
      </footer>
    </div>
  );
}
