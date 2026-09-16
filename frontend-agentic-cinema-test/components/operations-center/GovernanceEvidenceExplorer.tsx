import type { GovernanceTimelineEvent } from "../../services/governanceTimelineApi";

type Props = {
  events: GovernanceTimelineEvent[];
};

export default function GovernanceEvidenceExplorer({ events }: Props) {
  return (
    <section className="governance-section-card">
      <div className="governance-section-card__heading">
        <div>
          <span className="section-eyebrow">GOVERNANCE EVIDENCE</span>
          <h2>Audit Evidence</h2>
          <p>Evidence references remain visible to authorised operators.</p>
        </div>
      </div>

      <div className="evidence-card">
        <div className="evidence-card__icon">Y</div>

        <div>
          <h3>YETI&apos;s governance interpretation</h3>

          <p>
            Governance evidence records what happened, who performed the
            action, why it occurred and when it occurred.
          </p>

          <p>
            YETI explains evidence for human review. An authorised human
            operator remains responsible for the decision.
          </p>

          {events.length > 0 && (
            <p className="evidence-card__event-count">
              {events.length} governance event
              {events.length === 1 ? "" : "s"} currently available.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
