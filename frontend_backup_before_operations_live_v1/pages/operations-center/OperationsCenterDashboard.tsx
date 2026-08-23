import "./../../styles/operations-center-dashboard.css";

export default function OperationsCenterDashboard() {
  return (
    <main className="ops-center">
      <section className="ops-hero">
        <div>
          <small>EASYCHATBOT OPERATIONS CENTER</small>
          <h1>AI Operations Center</h1>
          <p>
            YETI provides operational visibility across governance,
            cybersecurity and provider controls. Human authority remains
            responsible for all operational decisions.
          </p>
          <span className="status-pill">● All systems operating normally</span>
        </div>

        <div className="yeti-card">
          <img
            src="/assets/characters/yeti-governance.png"
            alt="YETI Operations Guardian"
          />
          <strong>YETI</strong>
          <span>Operations Guardian</span>
        </div>
      </section>

      <section className="ops-grid">
        <article>
          <h2>Governance Center</h2>
          <p>Audit evidence, controls and governance visibility.</p>
          <button>Open Governance</button>
        </article>

        <article>
          <h2>Cybersecurity Center</h2>
          <p>Security intelligence and decision support.</p>
          <button>Open Cybersecurity</button>
        </article>

        <article>
          <h2>Provider Management</h2>
          <p>Controlled provider execution status.</p>
          <button>Open Providers</button>
        </article>

        <article>
          <h2>Runtime Health</h2>
          <p>Platform services and operational status.</p>
          <button>View Health</button>
        </article>
      </section>

      <section className="yeti-message">
        <h2>YETI Operational Brief</h2>
        <p>
          Everything looks calm from an operations perspective.
          Monitoring continues while authorised operators remain in control.
        </p>
      </section>
    </main>
  );
}