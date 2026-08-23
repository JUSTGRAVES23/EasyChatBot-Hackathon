import GovernanceNavigationButton from "./GovernanceNavigationButton";


export default function CybersecuritySidebarIntegration() {


    return (

        <div className="cybersecurity-navigation">


            <GovernanceNavigationButton

                label="Cybersecurity Dashboard"

                status="Monitoring"

                path="/cybersecurity"

            />


        </div>

    );

}