import { useMemo, useState } from "react";
import {
  submitGovernanceDecision,
  type GovernanceDecision,
  type GovernanceDecisionRequest,
  type GovernanceRole,
} from "../../lib/privacy-governance/decision-api";
import type {
  PrivacyGovernanceCaseDetail,
} from "../../lib/privacy-governance/types";
import styles from "./PrivacyGovernanceDecisionActions.module.css";

interface Props {
  caseData: PrivacyGovernanceCaseDetail;
  onDecisionComplete: (updatedCase: PrivacyGovernanceCaseDetail) => void;
}

function createApprovalId(
  caseId: string,
  role: GovernanceRole,
): string {
  const suffix =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

  return `APR-UI-${role}-${caseId}-${suffix}`;
}

function statusLabel(value?: string | null): string {
  if (!value) return "Unknown";
  return value.replaceAll("_", " ");
}

function decisionLabel(decision: GovernanceDecision): string {
  switch (decision) {
    case "approve":
      return "Approve";
    case "reject":
      return "Reject";
    case "request-changes":
      return "Request changes";
  }
}

export function PrivacyGovernanceDecisionActions({
  caseData,
  onDecisionComplete,
}: Props) {
  const [role, setRole] = useState<GovernanceRole>("DPO");
  const [reviewer, setReviewer] = useState("");
  const [comment, setComment] = useState("");

  const [pendingDecision, setPendingDecision] =
    useState<GovernanceDecision | null>(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isPending =
    caseData.governance_status === "PENDING_DPO_GRC";

  const approvalId = useMemo(
    () => createApprovalId(caseData.case_id, role),
    [caseData.case_id, role],
  );

  if (!isPending) {
    return (
      <section className={styles.section}>
        <div className={styles.completedCard}>
          <div>
            <span className={styles.eyebrow}>
              HUMAN GOVERNANCE DECISION
            </span>

            <strong>
              Governance decision recorded
            </strong>

            <p>
              This case is currently{" "}
              <b>{statusLabel(caseData.governance_status)}</b>.
              No additional decision is available while the
              case is outside the pending governance state.
            </p>
          </div>
        </div>
      </section>
    );
  }

  const canSubmit =
    reviewer.trim().length > 0 &&
    comment.trim().length > 0 &&
    Boolean(caseData.change_id) &&
    !submitting;

  async function executeDecision(
    decision: GovernanceDecision,
  ): Promise<void> {
    if (!caseData.change_id) {
      setError(
        "This governance case has no linked privacy change. "
        + "The decision cannot be submitted.",
      );
      return;
    }

    if (!reviewer.trim()) {
      setError("Reviewer identity is required.");
      return;
    }

    if (!comment.trim()) {
      setError("A decision comment is required.");
      return;
    }

    setSubmitting(true);
    setError(null);

    const request: GovernanceDecisionRequest = {
      change_id: caseData.change_id,
      approval_id: approvalId,
      reviewer: reviewer.trim(),
      role,
      comment: comment.trim(),
    };

    try {
      const result = await submitGovernanceDecision(
        caseData.case_id,
        decision,
        request,
      );

      onDecisionComplete(result.case);

      setPendingDecision(null);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Governance decision failed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className={styles.section}>
      <div className={styles.heading}>
        <div>
          <span className={styles.eyebrow}>
            HUMAN GOVERNANCE DECISION
          </span>

          <h3>Decision required</h3>

          <p>
            This case passed automated validation and is awaiting
            explicit human governance approval.
          </p>
        </div>

        <span className={styles.pendingBadge}>
          PENDING DPO/GRC
        </span>
      </div>

      <div className={styles.card}>
        <div className={styles.field}>
          <label htmlFor="governance-role">
            Decision role
          </label>

          <select
            id="governance-role"
            value={role}
            onChange={(event) =>
              setRole(event.target.value as GovernanceRole)
            }
            disabled={submitting}
          >
            <option value="DPO">
              DPO
            </option>

            <option value="GRC">
              GRC
            </option>
          </select>
        </div>

        <div className={styles.field}>
          <label htmlFor="governance-reviewer">
            Reviewer
          </label>

          <input
            id="governance-reviewer"
            type="text"
            value={reviewer}
            onChange={(event) =>
              setReviewer(event.target.value)
            }
            placeholder="Enter human reviewer name"
            disabled={submitting}
            autoComplete="off"
          />
        </div>

        <div className={styles.field}>
          <label htmlFor="governance-comment">
            Decision rationale
          </label>

          <textarea
            id="governance-comment"
            value={comment}
            onChange={(event) =>
              setComment(event.target.value)
            }
            placeholder="Record the reason for the governance decision."
            rows={4}
            disabled={submitting}
          />
        </div>

        {!caseData.change_id && (
          <div
            className={styles.warning}
            role="alert"
          >
            This case is missing its Change ID relationship.
            A governance decision is therefore blocked.
          </div>
        )}

        {error && (
          <div
            className={styles.error}
            role="alert"
          >
            {error}
          </div>
        )}

        <div className={styles.actions}>
          <button
            type="button"
            className={`${styles.actionButton} ${styles.approve}`}
            disabled={!canSubmit}
            onClick={() =>
              setPendingDecision("approve")
            }
          >
            Approve as {role}
          </button>

          <button
            type="button"
            className={`${styles.actionButton} ${styles.reject}`}
            disabled={!canSubmit}
            onClick={() =>
              setPendingDecision("reject")
            }
          >
            Reject
          </button>

          <button
            type="button"
            className={`${styles.actionButton} ${styles.changes}`}
            disabled={!canSubmit}
            onClick={() =>
              setPendingDecision("request-changes")
            }
          >
            Request changes
          </button>
        </div>
      </div>

      {pendingDecision && (
        <div
          className={styles.confirmBackdrop}
          role="presentation"
        >
          <div
            className={styles.confirmDialog}
            role="dialog"
            aria-modal="true"
            aria-labelledby="governance-confirm-title"
          >
            <span className={styles.eyebrow}>
              CONFIRM GOVERNANCE DECISION
            </span>

            <h3 id="governance-confirm-title">
              {decisionLabel(pendingDecision)}
            </h3>

            <p>
              You are about to record a formal human governance
              decision for:
            </p>

            <dl className={styles.confirmDetails}>
              <div>
                <dt>Case</dt>
                <dd>{caseData.case_id}</dd>
              </div>

              <div>
                <dt>Change</dt>
                <dd>{caseData.change_id}</dd>
              </div>

              <div>
                <dt>Role</dt>
                <dd>{role}</dd>
              </div>

              <div>
                <dt>Reviewer</dt>
                <dd>{reviewer}</dd>
              </div>
            </dl>

            <p className={styles.confirmWarning}>
              This action will be recorded as governance evidence
              and may change the governance state of the case.
            </p>

            <div className={styles.confirmActions}>
              <button
                type="button"
                className={styles.cancelButton}
                disabled={submitting}
                onClick={() =>
                  setPendingDecision(null)
                }
              >
                Cancel
              </button>

              <button
                type="button"
                className={`${styles.confirmButton} ${
                  pendingDecision === "approve"
                    ? styles.approve
                    : pendingDecision === "reject"
                      ? styles.reject
                      : styles.changes
                }`}
                disabled={submitting}
                onClick={() =>
                  void executeDecision(pendingDecision)
                }
              >
                {submitting
                  ? "Recording..."
                  : `Confirm ${decisionLabel(pendingDecision)}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default PrivacyGovernanceDecisionActions;