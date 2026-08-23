export default function GovernanceStatusCard(
    {status}: {status:string}
) {

    return (
        <section>
            <h2>
                Governance Status
            </h2>

            <p>
                {status}
            </p>
        </section>
    );
}
