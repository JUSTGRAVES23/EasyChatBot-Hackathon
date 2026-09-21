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
import ConfigurationOperationsCenterPage from "../app/operations-center/configuration/page";

import RiskIntelligencePage from "../app/operations-center/compliance/cmp/risk-intelligence/risk-coverage/page";

import WelcomePage from "../app/welcome/page";
import ProjectControlPage from "../app/project-control/page";
import ProjectRegistryPage from "../app/project-control/projects/page";
import ProjectControlProjectPage from "../app/project-control/projects/[projectId]/page";

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

function InvalidWorldPrivateChatUrlPage() {
  return (
    <main
      aria-label="Invalid World private chat URL"
      style={{
        maxWidth: 900,
        margin: "0 auto",
        padding: "2rem",
      }}
    >
      <h1>Invalid World chat URL</h1>

      <p>
        World private chat URLs identify the World only.
        Conversation IDs cannot be supplied in the URL.
      </p>

      <p>
        Please use the canonical World chat URL:
      </p>

      <code>/worlds/&lt;worldSlug&gt;/chat</code>
    </main>
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
          OPERATIONS CENTER CONFIGURATION
          Developer/Admin configuration and controlled settings
          Protected
          ========================================================= */}

      <Route
        path="/operations-center/configuration"
        element={
          <ProtectedRoute>
            <ConfigurationOperationsCenterPage />
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

      {/* Project Registry
          Authoritative project definitions used by Project Control.
          Protected */}
      <Route
        path="/project-control/projects"
        element={
          <ProtectedRoute>
            <ProjectRegistryPage />
          </ProtectedRoute>
        }
      />

      {/* Project Control — individual project detail
          Protected
          The projectId is taken from the canonical Project Registry
          project_id and is URL-encoded by the originating page. */}
      <Route
        path="/project-control/projects/:projectId"
        element={
          <ProtectedRoute>
            <ProjectControlProjectPage />
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
          M2-C3 — WORLD PRIVATE CHAT
          ========================================================= */}

      {/* M2-C3: Reject conversation IDs in public World URLs.
          A World URL identifies the World only.
          Conversation UUIDs remain server-side/internal.

          This route MUST appear before the generic catch-all so
          malformed World-chat URLs do not redirect to Operations
          Center. */}
      <Route
        path="/worlds/:worldSlug/chat/:conversationId"
        element={<InvalidWorldPrivateChatUrlPage />}
      />

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

      {/* =========================================================
          UNKNOWN ROUTES
          ========================================================= */}

      {/* Unknown routes return to the canonical Operations Center
          landing page rather than Functionality Health/Governance.

          The specific M2-C3 invalid World-chat route above prevents
          World chat URLs containing conversation IDs from reaching
          this catch-all. */}
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