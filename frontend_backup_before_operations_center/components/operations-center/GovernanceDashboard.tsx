/**
 * EasyChatBot Operations Center Governance Dashboard.
 *
 * YETI is the friendly governance guide.
 * Control authority remains in backend governance services.
 */

import YetiGovernanceAssistant from "./YetiGovernanceAssistant";

export default function GovernanceDashboard() {
  return (
    <main>
      <header>
        <h1>EasyChatBot Operations Center</h1>
        <h2>YETI Governance Guardian</h2>
        <p>
          Governance visibility, operational controls and audit evidence.
        </p>
      </header>

      <YetiGovernanceAssistant
        severity="warning"
        component="Provider delivery"
        reason="External provider security incident"
        actor="Admin"
        changedAt="10:42 CET"
      />

      <section>
        <h2>Governance Audit Events</h2>
        <p>
          Review who changed a control, why it changed and when it changed.
        </p>
      </section>

      <section>
        <h2>Control Status</h2>
        <p>
          Cybersecurity delivery, provider management and scheduler status
          remain controlled by backend governance services.
        </p>
      </section>
    </main>
  );
}
