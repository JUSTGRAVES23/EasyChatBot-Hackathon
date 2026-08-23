import DemoGovernanceTimeline from "./DemoGovernanceTimeline";
import DemoEvidencePanel from "./DemoEvidencePanel";
import DemoEmailPreview from "./DemoEmailPreview";
import DemoYetiAssistant from "./DemoYetiAssistant";


export default function OperationsCenterDemoPage(
    {data}: {data:any}
) {

    return (
        <main>

            <h1>
                EasyChatBot Operations Center
            </h1>


            <DemoGovernanceTimeline
                events={[data.timeline]}
            />


            <DemoEvidencePanel
                evidence={data.evidence}
            />


            <DemoEmailPreview
                email={data.email_preview}
            />


            <DemoYetiAssistant
                message={data.yeti}
            />

        </main>
    );
}
