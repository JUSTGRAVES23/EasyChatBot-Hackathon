import React from "react";

export default function YetiGovernanceTimelineAssistant({events = []}: {events?: any[]}) {

    const latest = events[0];

    return (
        <section>
            <h2>🧊 YETI Governance Assistant</h2>
            <p>
                {latest
                    ? `Governance event detected: ${latest.event} on ${latest.component}.`
                    : "No governance events require attention."
                }
            </p>
        </section>
    );
}
