import type { PrivacyGovernanceCase } from "../../lib/privacy-governance/types";

import styles from "./PrivacyGovernanceAssessmentResult.module.css";

type AssessmentResultStatus =
  | "APPROVED"
  | "REJECTED"
  | "BLOCKED";

interface PrivacyGovernanceAssessmentResultProps {
  caseData: PrivacyGovernanceCase;
  status: AssessmentResultStatus;
  onReturn: () => void;
}

const RESULT_CONFIG: Record<
  AssessmentResultStatus,
  {
    label: string;
    title: string;
    description: string;
    eyebrow: string;
  }
> = {
  APPROVED: {
    label: "CASE CLEARED",
    title: "Congratulations!",
    description:
      "The privacy governance assessment has been completed and the case has been approved.",
    eyebrow: "ASSESSMENT COMPLETED",
  },

  REJECTED: {
    label: "CASE REJECTED",
    title: "Assessment completed",
    description:
      "The privacy governance assessment has been completed and the case has been rejected.",
    eyebrow: "ASSESSMENT COMPLETED",
  },

  BLOCKED: {
    label: "CASE BLOCKED",
    title: "Assessment completed",
    description:
      "The privacy governance assessment has been completed and the case is blocked.",
    eyebrow: "ASSESSMENT COMPLETED",
  },
};

function formatStatus(value: string): string {
  return value.replaceAll("_", " ");
}

export default function PrivacyGovernanceAssessmentResult({
  caseData,
  status,
  onReturn,
}: PrivacyGovernanceAssessmentResultProps) {
  const config = RESULT_CONFIG[status];

  return (
    <main
      className={styles.page}
      aria-label="Privacy governance assessment result"
    >
      <section
        className={`${styles.card} ${styles[status.toLowerCase()]}`}
      >
        <p className={styles.eyebrow}>
          EASYCHATBOT · PRIVACY GOVERNANCE
        </p>

        <p className={styles.completed}>
          {config.eyebrow}
        </p>

        <div
          className={styles.statusIcon}
          aria-hidden="true"
        >
          {status === "APPROVED" && "✓"}
          {status === "REJECTED" && "×"}
          {status === "BLOCKED" && "!"}
        </div>

        <p className={styles.statusLabel}>
          {config.label}
        </p>

        <h1>{config.title}</h1>

        <p className={styles.caseTitle}>
          {caseData.title}
        </p>

        <p className={styles.description}>
          {config.description}
        </p>

        <div className={styles.mascotArea}>
          <img
            src="/assets/easychatbot-mascot.png"
            alt="EasyChatBot mascot"
            className={styles.mascot}
          />
        </div>

        <div className={styles.caseSummary}>
          <div>
            <span>Case ID</span>
            <strong>{caseData.case_id}</strong>
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
              {caseData.risk
                ? formatStatus(caseData.risk)
                : "—"}
            </strong>
          </div>

          <div>
            <span>Final status</span>
            <strong>
              {formatStatus(
                caseData.governance_status,
              )}
            </strong>
          </div>
        </div>

        <p className={styles.completionNote}>
          DPO and GRC assessment completed for
          this case.
        </p>

        <button
          type="button"
          className={styles.button}
          onClick={onReturn}
        >
          Return to Governance Center
        </button>
      </section>
    </main>
  );
}