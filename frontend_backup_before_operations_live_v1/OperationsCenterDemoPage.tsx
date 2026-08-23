import DemoScenarioSelector from "./DemoScenarioSelector";
import CybersecurityDemoView from "./CybersecurityDemoView";
import ProviderManagementDemoView from "./ProviderManagementDemoView";
import YetiConversationCard from "./YetiConversationCard";

export default function OperationsCenterDemoPage() {

    return (
        <main>
            <h1>
                EasyChatBot AI Operations Center Demo
            </h1>

            <DemoScenarioSelector />

            <CybersecurityDemoView />

            <ProviderManagementDemoView />

            <YetiConversationCard
                message={
                    "I detected a governance event. " +
                    "Evidence has been preserved."
                }
            />
        </main>
    );
}
