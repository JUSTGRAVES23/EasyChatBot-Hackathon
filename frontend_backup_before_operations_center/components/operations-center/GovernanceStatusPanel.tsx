import type { GovernanceStatus } from "../../services/governanceApi";

type Props = {
  data: GovernanceStatus;
};

function titleForComponent(component: string): string {
  const titles: Record<string, string> = {
    provider_management: "Provider Controls",
    cybersecurity_delivery: "Cybersecurity Governance",
  };

  return titles[component] ?? component.replaceAll("_", " ");
}

export default function GovernanceStatusPanel({ data }: Props) {
  const provider = data.controls.find(
    (control) => control.component === "provider_management",
  );

  const cybersecurity = data.controls.find(
    (control) => control.component === "cybersecurity_delivery",
  );

  const cards = [
    {
      key: "governance",
      eyebrow: "GOVERNANCE STATUS",
      title: data.recent_events.length ? "Attention" : "Healthy",
      description: data.recent_events.length
        ? "Recent governance activity has been recorded for operator review."
        : "No active governance alert has been recorded.",
      explanation: data.yeti.message,
      healthy: !data.recent_events.length,
    },
    {
      key: "provider",
      eyebrow: "PROVIDER CONTROLS",
      title: provider?.status === "paused" ? "Paused" : "Active",
      description:
        provider?.status === "paused"
          ? provider.details.reason ?? "Provider delivery is paused."
          : "Provider delivery is currently operating normally.",
      explanation:
        provider?.status === "paused"
          ? `YETI explains: ${provider.details.reason ?? "Provider delivery is paused."}`
          : "YETI explains: No provider pause is currently recorded.",
      healthy: provider?.status !== "paused",
    },
    {
      key: "cybersecurity",
      eyebrow: "CYBERSECURITY GOVERNANCE",
      title: cybersecurity?.status === "paused" ? "Paused" : "Monitored",
      description:
        cybersecurity?.status === "paused"
          ? cybersecurity.details.reason ?? "Cybersecurity delivery is paused."
          : "No cybersecurity delivery pause is currently recorded.",
      explanation:
        cybersecurity?.status === "paused"
          ? `YETI explains: ${cybersecurity.details.reason ?? "Cybersecurity delivery is paused."}`
          : "YETI explains: Cybersecurity signals are surfaced for governance review. Remediation remains outside YETI's authority.",
      healthy: cybersecurity?.status !== "paused",
    },
  ];

  return (
    <section className="governance-status-grid" aria-label="Governance status">
      {cards.map((card) => (
        <article className="governance-panel-card" key={card.key}>
          <div className="governance-panel-card__topline">
            <span className="governance-panel-card__eyebrow">
              {card.eyebrow}
            </span>

            <span
              className={`status-dot ${
                card.healthy ? "status-dot--healthy" : "status-dot--alert"
              }`}
              aria-label={card.healthy ? "Healthy" : "Attention required"}
            >
              ✓
            </span>
          </div>

          <h2>{card.title}</h2>
          <p className="governance-panel-card__description">
            {card.description}
          </p>

          <div className="yeti-explanation">
            <strong>YETI explains</strong>
            <span>{card.explanation}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
