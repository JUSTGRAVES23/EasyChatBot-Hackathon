import type { GovernanceTimelineEvent } from "../../services/governanceTimelineApi";

type Props = {
  events: GovernanceTimelineEvent[];
};

export default function GovernanceTimelinePanel({ events }: Props) {
  return (
    <section className="governance-section-card">
      <div className="governance-section-card__heading">
        <div>
          <span className="section-eyebrow">AUDIT & GOVERNANCE</span>
          <h2>Governance Events</h2>
          <p>
            Chronological evidence of governance activity and authorised
            operational changes.
          </p>
        </div>

        <span className="section-count">{events.length}</span>
      </div>

      {events.length === 0 ? (
        <div className="empty-governance-state">
          <strong>No governance events currently available.</strong>
          <span>YETI has no recent governance event to interpret.</span>
        </div>
      ) : (
        <div className="governance-events">
          {events.map((event, index) => (
            <article className="governance-event" key={event.event_id ?? `${event.event}-${index}`}>
              <div className="governance-event__marker" />

              <div>
                <strong>{event.event}</strong>
                <p>{event.reason}</p>
                <small>
                  {event.component} · {event.actor} · {event.timestamp}
                </small>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
