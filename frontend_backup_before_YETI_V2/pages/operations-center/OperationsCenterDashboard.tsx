import { useOperationsCenter } from "../../hooks/useOperationsCenter";
import HealthMetricCard from "../../components/operations-center/HealthMetricCard";
import YetiBriefCard from "../../components/operations-center/YetiBriefCard";
import "../../styles/operations-center-dashboard.css";

export default function OperationsCenterDashboard() {
  const { data, loading } = useOperationsCenter();

  return (
    <main className="ops-center">
      <section className="ops-hero">
        <div>
          <small>EASYCHATBOT OPERATIONS CENTER</small>
          <h1>AI Operations Center</h1>
          <p>
            Operational visibility across governance, cybersecurity and
            provider controls.
          </p>
        </div>

        <img
          className="yeti-image"
          src="/assets/characters/yeti-governance.png"
          alt="YETI"
        />
      </section>

      {loading ? (
        <section className="ops-card">Loading operational data...</section>
      ) : (
        <>
          <HealthMetricCard />
          <YetiBriefCard />

          <section className="ops-grid">
            <div className="ops-card">
              <h2>Governance</h2>
              <p>{data?.governance?.yeti?.message}</p>
            </div>

            <div className="ops-card">
              <h2>Provider Management</h2>
              <p>
                {data?.provider?.paused
                  ? "Provider paused"
                  : "Provider operating normally"}
              </p>
            </div>
          </section>
        </>
      )}
    </main>
  );
}