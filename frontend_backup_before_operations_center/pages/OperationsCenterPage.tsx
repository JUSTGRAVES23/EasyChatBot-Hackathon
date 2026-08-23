import YetiPanel from "../components/operations-center/YetiPanel";
import GovernanceTimeline from "../components/operations-center/GovernanceTimeline";
import EvidenceExplorer from "../components/operations-center/EvidenceExplorer";
import EmailPreview from "../components/operations-center/EmailPreview";
import GovernanceStatusCard from "../components/operations-center/GovernanceStatusCard";


export default function OperationsCenterPage() {

    const demoData = {
        status: "Operational",
        events: [
            {
                id: "EVT-001",
                event: "CYBERSECURITY_ALERT",
                component: "email_delivery",
                severity: "CRITICAL",
            }
        ],
        evidence: {
            available: true,
            records: 3,
        },
        email: {
            subject:
                "[CRITICAL] Cybersecurity Incident Detected",
            status:
                "Prepared",
        },
        yeti:
            "I detected a governance event. Controls were followed and evidence has been preserved.",
    };


    return (
        <main>

            <h1>
                EasyChatBot AI Operations Center
            </h1>


            <GovernanceStatusCard
                status={demoData.status}
            />


            <YetiPanel
                message={demoData.yeti}
            />


            <GovernanceTimeline
                events={demoData.events}
            />


            <EvidenceExplorer
                evidence={demoData.evidence}
            />


            <EmailPreview
                email={demoData.email}
            />

        </main>
    );
}
