import OperationsDomainCard from "./OperationsDomainCard";

export default function OperationsNavigation() {
  return (
    <div className="operations-grid">
      <OperationsDomainCard
        title="Governance"
        status="Healthy"
        description="Governance controls and audit visibility."
        link="/operations-center/governance"
      />
      <OperationsDomainCard
        title="Cybersecurity"
        status="Monitoring"
        description="Cybersecurity intelligence visibility."
        link="/operations-center/cybersecurity"
      />
      <OperationsDomainCard
        title="Provider Management"
        status="Healthy"
        description="Approved provider operational controls."
        link="/operations-center/providers"
      />
    </div>
  );
}
