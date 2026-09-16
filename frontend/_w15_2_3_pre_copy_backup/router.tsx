import {
  Navigate,
  Route,
  Routes,
  useSearchParams,
} from "react-router-dom";

import OperationsCenterGovernancePage from "../app/operations-center/governance/page";
import OperationsCenterPage from "../pages/OperationsCenterPage";

import PrivacyGovernancePage from "../app/privacy-governance/page";

import FunctionalityHealthPage from "../app/operations-center/functionality-health/page";
import EmailWorkflowsPage from "../app/operations-center/email-workflows/page";

import PersistenceOperationsPage from "../app/operations-center/persistence/page";
import PersistenceHealthPage from "../app/operations-center/persistence/health/page";

import RiskIntelligencePage from "../app/operations-center/compliance/cmp/risk-intelligence/risk-coverage/page";

import WelcomePage from "../app/welcome/page";
import ProjectControlPage from "../app/project-control/page";

import LoginPage from "../app/login/page";
import RegisterPage from "../app/register/page";
import VerifyEmailPage from "../app/verify-email/page";
import ForgotPasswordPage from "../app/forgot-password/page";
import ResetPasswordPage from "../app/reset-password/page";

import CinemaPage from "./agentic-cinema/CinemaPage";
import QuestionnaireSelectionPage from "./academy/questionnaires/QuestionnaireSelectionPage";
import ProtectedRoute from "./auth/ProtectedRoute";
import WorldPrivateChatPage from "./worlds/WorldPrivateChatPage";

function AcademyQuestionnairesRoute() {
  const [searchParams] = useSearchParams();

  const worldId =
    searchParams.get("world")?.trim().toLowerCase() ||
    "french";

  return (
    <QuestionnaireSelectionPage
      worldId={worldId}
    />
  );
}

export default function AppRouter() {
  return (
    <Routes>
      {/* =========================================================
          AUTHENTICATION
          Public
          ========================================================= */}

      {/* Sign in */}
      <Route
        path="/login"
        element={<LoginPage />}
      />

      {/* Registration */}
      <Route
        path="/register"
        element={<RegisterPage />}
      />

      {/* Email verification */}
      <Route
        path="/verify-email"
        element={<VerifyEmailPage />}
      />

      {/* Password reset request */}
      <Route
        path="/forgot-password"
        element={<ForgotPasswordPage />}
      />

      {/* Password reset confirmation */}
      <Route
        path="/reset-password"
        element={<ResetPasswordPage />}
      />

      {/* =========================================================
          AGENTIC CINEMA
          Hackathon feature
          Public for current slice
          ========================================================= */}

      <Route
        path="/agentic-cinema"
        element={<CinemaPage />}
      />

      {/* =========================================================
          ACADEMY
          ========================================================= */}

      {/* Academy Welcome */}
      <Route
        path="/welcome"
        element={<WelcomePage />}
      />

      {/* Academy Questionnaire Selection */}
      <Route
        path="/questionnaires"
        element={<AcademyQuestionnairesRoute />}
      />

      {/* =========================================================
          OPERATIONS CENTER
          Protected
          ========================================================= */}

      {/* Operations Center root / landing page */}
      <Route
        path="/operations-center"
        element={
          <ProtectedRoute>
            <OperationsCenterPage />
          </ProtectedRoute>
        }
      />

      {/* =========================================================
          PERSISTENCE OPERATIONS
          PostgreSQL / Database Operations
          Protected
          ========================================================= */}

      {/* Persistence Operations overview / decision layer */}
      <Route
        path="/operations-center/persistence"
        element={
          <ProtectedRoute>
            <PersistenceOperationsPage />
          </ProtectedRoute>
        }
      />

      {/* Database Health & Operations
          PostgreSQL diagnostics / operational health */}
      <Route
        path="/operations-center/persistence/health"
        element={
          <ProtectedRoute>
            <PersistenceHealthPage />
          </ProtectedRoute>
        }
      />

      {/* =========================================================
          FUNCTIONALITY HEALTH
          Application / feature functionality monitoring
          This is NOT PostgreSQL health.
          ========================================================= */}

      <Route
        path="/operations-center/functionality-health"
        element={
          <ProtectedRoute>
            <FunctionalityHealthPage />
          </ProtectedRoute>
        }
      />

      {/* =========================================================
          OPERATIONS CENTER EMAIL WORKFLOWS
          Protected
          ========================================================= */}

      <Route
        path="/operations-center/email-workflows"
        element={
          <ProtectedRoute>
            <EmailWorkflowsPage />
          </ProtectedRoute>
        }
      />

      {/* =========================================================
          OPERATIONS CENTER GOVERNANCE
          Protected
          ========================================================= */}

      <Route
        path="/operations-center/governance"
        element={
          <ProtectedRoute>
            <OperationsCenterGovernancePage />
          </ProtectedRoute>
        }
      />

      {/* =========================================================
          COMPLIANCE → CMP → RISK INTELLIGENCE
          Protected
          ========================================================= */}

      {/* Compliance → CMP → Risk Intelligence → Risk Coverage */}
      <Route
        path="/operations-center/compliance/cmp/risk-intelligence/risk-coverage"
        element={
          <ProtectedRoute>
            <RiskIntelligencePage />
          </ProtectedRoute>
        }
      />

      {/* Backward-compatible redirect for the initial Risk
          Intelligence URL */}
      <Route
        path="/operations-center/risk-intelligence"
        element={
          <Navigate
            to="/operations-center/compliance/cmp/risk-intelligence/risk-coverage"
            replace
          />
        }
      />

      {/* =========================================================
          PRIVACY GOVERNANCE
          Protected
          ========================================================= */}

      {/* Privacy Governance dashboard */}
      <Route
        path="/privacy-governance"
        element={
          <ProtectedRoute>
            <PrivacyGovernancePage />
          </ProtectedRoute>
        }
      />

      {/* Privacy Governance specific case */}
      <Route
        path="/privacy-governance/:caseId"
        element={
          <ProtectedRoute>
            <PrivacyGovernancePage />
          </ProtectedRoute>
        }
      />

      {/* =========================================================
          PROJECT CONTROL
          Protected
          ========================================================= */}

      {/* Project Control Center */}
      <Route
        path="/project-control"
        element={
          <ProtectedRoute>
            <ProjectControlPage />
          </ProtectedRoute>
        }
      />

      {/* =========================================================
          APPLICATION ROOT
          ========================================================= */}

      {/* Application root
          Reuse the Operations Center landing page. */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <OperationsCenterPage />
          </ProtectedRoute>
        }
      />

      {/* =========================================================
          UNKNOWN ROUTES
          ========================================================= */}

      {/* Unknown routes return to the canonical Operations Center
          landing page rather than Functionality Health/Governance. */}
      {/* M2-C3: Generic protected World private chat.
          The URL contains the World slug only.
          Conversation UUIDs remain server-side/internal. */}
      <Route
        path="/worlds/:worldSlug/chat"
        element={
          <ProtectedRoute>
            <WorldPrivateChatPage />
          </ProtectedRoute>
        }
      />
      
      <Route
        path="*"
        element={
          <Navigate
            to="/operations-center"
            replace
          />
        }
      />
    </Routes>
  );
}


