export default function DemoEvidencePanel(
    {evidence}: {evidence:any}
) {

    return (
        <section>
            <h2>Evidence Explorer</h2>

            <p>
                Available:
                {evidence.available ? " Yes" : " No"}
            </p>

            <p>
                {evidence.reason}
            </p>
        </section>
    );
}
