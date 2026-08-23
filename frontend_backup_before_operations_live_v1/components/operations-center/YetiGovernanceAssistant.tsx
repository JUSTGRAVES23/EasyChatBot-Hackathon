type GovernanceAssistantProps = {
  severity: "info" | "warning" | "critical";
  component: string;
  reason: string;
  actor: string;
  changedAt: string;
  message?: string;
};

const severityLabel = {
  info: "Governance operating normally",
  warning: "Governance attention required",
  critical: "Critical governance attention required",
} as const;

export default function YetiGovernanceAssistant({
  severity,
  component,
  reason,
  actor,
  changedAt,
  message,
}: GovernanceAssistantProps) {
  return (
    <section className={`yeti-brief yeti-brief--${severity}`}>
      <div className="yeti-brief__eyebrow">YETI GOVERNANCE BRIEF</div>

      <div className="yeti-brief__content">
        <div>
          <h2>
            {message ??
              (severity === "info"
                ? "Everything looks calm from a governance perspective."
                : severityLabel[severity])}
          </h2>

          <p className="yeti-brief__summary">
            YETI explains governance state and evidence. YETI cannot approve,
            pause, resume or execute operational controls.
          </p>

          <div className="yeti-brief__facts">
            <span>{component}</span>
            <span>{actor}</span>
            <span>{changedAt}</span>
          </div>

          <p className="yeti-brief__reason">
            <strong>YETI interpretation:</strong> {reason}
          </p>
        </div>
      </div>
    </section>
  );
}
