export default function DemoGovernanceTimeline(
    {events}: {events:any[]}
) {

    return (
        <section>
            <h2>Governance Timeline</h2>

            {events.map((event, index) => (
                <div key={index}>
                    {event.event}
                    {" - "}
                    {event.component}
                </div>
            ))}

        </section>
    );
}
