import OperationsCenterShell from "@/app/components/operations-center/OperationsCenterShell";
import FunctionalityHealthDashboard from "@/app/components/operations-center/functionality-health/FunctionalityHealthDashboard";

export default function FunctionalityHealthPage() {
  return (
    <OperationsCenterShell>
      <FunctionalityHealthDashboard />
    </OperationsCenterShell>
  );
}
