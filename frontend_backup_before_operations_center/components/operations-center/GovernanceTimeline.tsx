export default function GovernanceTimeline(
    {events}: {events:any[]}
) {

    return (
        <section>
            <h2>
                Governance Timeline
            </h2>

            {events.map(event => (
                <article key={event.id}>
                    <strong>
                        {event.event}
                    </strong>

                    <p>
                        Component:
                        {event.component}
                    </p>

                    <p>
                        Severity:
                        {event.severity}
                    </p>
                </article>
            ))}

        </section>
    );
}
