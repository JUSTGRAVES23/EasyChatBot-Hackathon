export default function EvidenceExplorer(
    {evidence}: {evidence:any}
) {

    return (
        <section>
            <h2>
                Evidence Explorer
            </h2>

            <p>
                Evidence Available:
                {evidence.available ? " YES" : " NO"}
            </p>

            <p>
                Records:
                {evidence.records}
            </p>
        </section>
    );
}
