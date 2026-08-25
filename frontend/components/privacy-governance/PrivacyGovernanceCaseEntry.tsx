import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getPrivacyGovernanceCase,
} from "../../lib/privacy-governance/api";

import type {
  PrivacyGovernanceCase,
} from "../../lib/privacy-governance/types";

import styles from "./PrivacyGovernanceCaseEntry.module.css";

function isCleared(
  governanceStatus?: string | null,
): boolean {
  return (
    governanceStatus?.toUpperCase() === "APPROVED"
  );
}

function statusLabel(
  value?: string | null,
): string {
  if (!value) {
    return "Unknown";
  }

  return value.replaceAll("_", " ");
}

export default function PrivacyGovernanceCaseEntry() {
  const { caseId } = useParams<{
    caseId?: string;
  }>();

  const navigate = useNavigate();

  const [caseData, setCaseData] =
    useState<PrivacyGovernanceCase | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  /*
   * ============================================================
   * LOAD AUTHORITATIVE CASE
   * ============================================================
   */

  useEffect(() => {
    let cancelled = false;

    async function loadCase(): Promise<void> {
      if (!caseId) {
        setError(
          "Privacy governance case ID is missing.",
        );
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const result =
          await getPrivacyGovernanceCase(caseId);

        if (!cancelled) {
          setCaseData(result);
        }
      } catch (cause) {
        if (!cancelled) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load the privacy governance case.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadCase();

    return () => {
      cancelled = true;
    };
  }, [caseId]);

  /*
   * ============================================================
   * REDIRECT NON-CLEARED CASES
   *
   * IMPORTANT:
   * Navigation must happen inside useEffect, never during render.
   *
   * Existing dashboard remains the authoritative review surface.
   * ============================================================
   */

  useEffect(() => {
    if (
      !loading &&
      caseData &&
      !isCleared(caseData.governance_status)
    ) {
      navigate(
        `/privacy-governance?caseId=${encodeURIComponent(
          caseData.case_id,
        )}`,
        {
          replace: true,
        },
      );
    }
  }, [
    loading,
    caseData,
    navigate,
  ]);

  /*
   * ============================================================
   * LOADING
   * ============================================================
   */

  if (loading) {
    return (
      <main
        className={styles.page}
        aria-label="Privacy governance case"
      >
        <section
          className={styles.stateCard}
          role="status"
        >
          <p className={styles.eyebrow}>
            PRIVACY GOVERNANCE
          </p>

          <h1>
            Loading case...
          </h1>

          <p>
            Retrieving the authoritative governance
            record.
          </p>
        </section>
      </main>
    );
  }

  /*
   * ============================================================
   * ERROR
   * ============================================================
   */

  if (error || !caseData) {
    return (
      <main
        className={styles.page}
        aria-label="Privacy governance case"
      >
        <section
          className={styles.stateCard}
          role="alert"
        >
          <p className={styles.eyebrow}>
            PRIVACY GOVERNANCE
          </p>

          <h1>
            Unable to open case
          </h1>

          <p>
            {error ??
              "The requested governance case could not be found."}
          </p>

          <button
            type="button"
            className={styles.primaryButton}
            onClick={() =>
              navigate("/privacy-governance")
            }
          >
            Return to Governance Center
          </button>
        </section>
      </main>
    );
  }

  /*
   * ============================================================
   * NOT CLEARED
   *
   * The redirect is handled by the useEffect above.
   * Keep this render lightweight while navigation occurs.
   * ============================================================
   */

  if (!isCleared(caseData.governance_status)) {
    return (
      <main
        className={styles.page}
        aria-label="Privacy governance case"
      >
        <section
          className={styles.stateCard}
          role="status"
        >
          <p className={styles.eyebrow}>
            PRIVACY GOVERNANCE
          </p>

          <h1>
            Opening case review...
          </h1>

          <p>
            Opening the existing Governance Center
            review for this case.
          </p>
        </section>
      </main>
    );
  }

  /*
   * ============================================================
   * APPROVED
   *
   * Terminal success screen.
   *
   * This screen appears ONLY after the authoritative
   * governance record says APPROVED.
   * ============================================================
   */

  return (
    <main
      className={styles.page}
      aria-label="Privacy governance case cleared"
    >
      <section
        className={styles.clearedCard}
      >
        <p className={styles.eyebrow}>
          EASYCHATBOT · PRIVACY GOVERNANCE
        </p>

        <div
          className={styles.successIcon}
          aria-hidden="true"
        >
          ✓
        </div>

        <p className={styles.successLabel}>
          CASE CLEARED
        </p>

        <h1>
          Congratulations!
        </h1>

        <p className={styles.caseTitle}>
          {caseData.title}
        </p>

        <p className={styles.description}>
          This privacy governance case has
          been successfully reviewed and
          cleared.
        </p>

        <div className={styles.caseSummary}>
          <div>
            <span>Case ID</span>
            <strong>
              {caseData.case_id}
            </strong>
          </div>

          <div>
            <span>Change ID</span>
            <strong>
              {caseData.change_id || "—"}
            </strong>
          </div>

          <div>
            <span>Risk</span>
            <strong>
              {statusLabel(caseData.risk)}
            </strong>
          </div>

          <div>
            <span>Governance status</span>
            <strong>
              {statusLabel(
                caseData.governance_status,
              )}
            </strong>
          </div>
        </div>

        <div className={styles.mascotArea}>
          <img
  src="/assets/mascot/welcome-sign-up-mascot.png"
  alt="EasyChatBot mascot"
  className={styles.mascot}
/>
        </div>

        <p className={styles.authoritativeNote}>
          The governance record remains the
          authoritative record for this case.
        </p>

        <button
          type="button"
          className={styles.secondaryButton}
          onClick={() =>
            navigate("/privacy-governance")
          }
        >
          Return to Governance Center
        </button>
      </section>
    </main>
  );
}