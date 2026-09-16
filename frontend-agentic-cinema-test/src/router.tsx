import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import OperationsCenterGovernancePage from "../app/operations-center/governance/page";
import PrivacyGovernancePage from "../app/privacy-governance/page";
import FunctionalityHealthPage from "../app/operations-center/functionality-health/page";
import EmailWorkflowsPage from "../app/operations-center/email-workflows/page";
import RiskIntelligencePage from "../app/operations-center/compliance/cmp/risk-intelligence/risk-coverage/page";
import WelcomePage from "../app/welcome/page";
import ProjectControlPage from "../app/project-control/page";

/*
 * Agentic Cinema
 *
 * The Cinema feature is integrated into the existing Vite + React
 * application. It is intentionally NOT mounted as a second Next.js
 * application.
 */
import { CinemaApp } from "./agentic-cinema/CinemaApp";

export default function AppRouter() {
  return (
    <Routes>
      {/* ================================================================
          Academy Welcome
          ================================================================ */}
      <Route
        path="/welcome"
        element={<WelcomePage />}
      />

      {/* ================================================================
          Agentic Cinema
          
          Explicit product route.
          
          IMPORTANT:
          /agentic-cinema must be registered before the catch-all route
          below. Otherwise React Router will redirect it to Governance.
          ================================================================ */}
      <Route
        path="/agentic-cinema"
        element={<CinemaApp />}
      />

      {/* ================================================================
          Operations Center Governance
          ================================================================ */}
      <Route
        path="/operations-center/governance"
        element={<OperationsCenterGovernancePage />}
      />

      {/* ================================================================
          Operations Center Functionality Health
          ================================================================ */}
      <Route
        path="/operations-center/functionality-health"
        element={<FunctionalityHealthPage />}
      />

      {/* ================================================================
          Operations Center Email Workflows
          ================================================================ */}
      <Route
        path="/operations-center/email-workflows"
        element={<EmailWorkflowsPage />}
      />

      {/* ================================================================
          Compliance ? CMP ? Risk Intelligence ? Risk Coverage
          ================================================================ */}
      <Route
        path="/operations-center/compliance/cmp/risk-intelligence/risk-coverage"
        element={<RiskIntelligencePage />}
      />

      {/* ================================================================
          Backward-compatible Risk Intelligence redirect
          ================================================================ */}
      <Route
        path="/operations-center/risk-intelligence"
        element={
          <Navigate
            to="/operations-center/compliance/cmp/risk-intelligence/risk-coverage"
            replace
          />
        }
      />

      {/* ================================================================
          Privacy Governance dashboard
          ================================================================ */}
      <Route
        path="/privacy-governance"
        element={<PrivacyGovernancePage />}
      />

      {/* ================================================================
          Privacy Governance specific case
          ================================================================ */}
      <Route
        path="/privacy-governance/:caseId"
        element={<PrivacyGovernancePage />}
      />

      {/* ================================================================
          Project Control Center
          ================================================================ */}
      <Route
        path="/project-control"
        element={<ProjectControlPage />}
      />

      {/* ================================================================
          Application root
          
          Existing behaviour intentionally preserved:
          / ? /operations-center/governance
          ================================================================ */}
      <Route
        path="/"
        element={
          <Navigate
            to="/operations-center/governance"
            replace
          />
        }
      />

      {/* ================================================================
          Unknown routes
          
          Existing fallback intentionally preserved.
          Only genuinely unknown URLs go to Governance.
          ================================================================ */}
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
