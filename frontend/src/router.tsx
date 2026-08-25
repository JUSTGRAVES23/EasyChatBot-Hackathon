import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import OperationsCenterGovernancePage from "../app/operations-center/governance/page";
import PrivacyGovernancePage from "../app/privacy-governance/page";

export default function AppRouter() {
  return (
    <Routes>
      {/* Operations Center Governance */}
      <Route
        path="/operations-center/governance"
        element={<OperationsCenterGovernancePage />}
      />

      {/* Privacy Governance dashboard */}
      <Route
        path="/privacy-governance"
        element={<PrivacyGovernancePage />}
      />

      {/* Privacy Governance specific case */}
      <Route
        path="/privacy-governance/:caseId"
        element={<PrivacyGovernancePage />}
      />

      {/* Application root */}
      <Route
        path="/"
        element={
          <Navigate
            to="/operations-center/governance"
            replace
          />
        }
      />

      {/* Unknown routes */}
      <Route
        path="*"
        element={
          <Navigate
            to="/operations-center/governance"
            replace
          />
        }
      />
    </Routes>
  );
}