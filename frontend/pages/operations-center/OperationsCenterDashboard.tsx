import OperationsNavigation from "../../components/operations-center/OperationsNavigation";

export default function OperationsCenterDashboard() {
  return (
    <main className="operations-center">
      <section className="hero">
        <div>
          <small>EASYCHATBOT OPERATIONS CENTER</small>
          <h1>AI Operations Center</h1>
          <p>
            Operational visibility across governance, cybersecurity and provider controls.
          </p>
        </div>
        <img src="/assets/characters/yeti-governance.png" alt="YETI"/>
      </section>

      <section className="card">
        <h2>Operations Health</h2>
        <h1>96%</h1>
        <div className="health-bar"><span/></div>
        <p>All operational controls are operating normally.</p>
      </section>

      <section className="card">
        <small>YETI OPERATIONAL BRIEF</small>
        <h2>Everything looks calm from an operations perspective.</h2>
        <p>YETI explains operational state while authorised humans remain responsible for decisions.</p>
      </section>

      <OperationsNavigation />
    </main>
  );
}
