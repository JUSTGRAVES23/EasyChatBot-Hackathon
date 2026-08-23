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
      <Route
        path="/operations-center/governance"
        element={<OperationsCenterGovernancePage />}
      />

      {/* Privacy Governance dashboard */}
      <Route
        path="/privacy-governance"
        element={<PrivacyGovernancePage />}
      />

      {/* Privacy Governance dashboard with a specific case opened */}
      <Route
        path="/privacy-governance/:caseId"
        element={<PrivacyGovernancePage />}
      />

      <Route
        path="/"
        element={
          <Navigate
            to="/operations-center/governance"
            replace
          />
        }
      />

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