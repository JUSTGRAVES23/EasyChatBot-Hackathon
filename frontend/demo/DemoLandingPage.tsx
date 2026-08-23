import ScenarioSelector from "./ScenarioSelector";
import DemoStatusBanner from "./DemoStatusBanner";


export default function DemoLandingPage() {

    return (
        <main>

            <DemoStatusBanner />

            <h1>
                EasyChatBot Demo Environment
            </h1>

            <ScenarioSelector />

        </main>
    );
}
