import {
  useMemo,
  useState,
} from "react";

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
  /**
   * Preferred public prop name.
   */
  caseDetail?: PrivacyGovernanceCaseDetail;

  /**
   * Backward-compatible prop used by the
   * existing case-detail component.
   */
  caseData?: PrivacyGovernanceCaseDetail;

  /**
   * Preferred callback name.
   */
  onDecisionCompleted?: (
    updatedCase: PrivacyGovernanceCaseDetail,
  ) => void;

  /**
   * Backward-compatible callback name.
   */
  onDecisionComplete?: (
    updatedCase: PrivacyGovernanceCaseDetail,
  ) => void;
}

function createApprovalId(
  caseId: string,
  role: GovernanceRole,
): string {
  const randomUuid =
    typeof crypto !== "undefined" &&
    typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random()
          .toString(36)
          .slice(2, 10)}`;

  return `APR-UI-${role}-${caseId}-${randomUuid}`;
}

function statusLabel(
  value?: string | null,
): string {
  if (!value) {
    return "Unknown";
  }

  return value.replaceAll("_", " ");
}

function decisionLabel(
  decision: GovernanceDecision,
): string {
  switch (decision) {
    case "approve":
      return "Approve";

    case "reject":
      return "Reject";

    case "request-changes":
      return "Request changes";

    default:
      return "Decision";
  }
}

export function PrivacyGovernanceDecisionActions({
  caseDetail,
  caseData,
  onDecisionCompleted,
  onDecisionComplete,
}: Props) {
  /*
   * Resolve the case from the preferred or
   * backward-compatible prop.
   */
  const resolvedCase =
    caseDetail ?? caseData ?? null;

  /*
   * Resolve the preferred or backward-compatible
   * completion callback.
   */
  const handleDecisionCompleted =
    onDecisionCompleted ??
    onDecisionComplete;

  /*
   * Hooks must always execute in the same order.
   */
  const [role, setRole] =
    useState<GovernanceRole>("DPO");

  const [reviewer, setReviewer] =
    useState("");

  const [comment, setComment] =
    useState("");

  const [pendingDecision, setPendingDecision] =
    useState<GovernanceDecision | null>(
      null,
    );

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  /*
   * Generate the approval evidence identifier
   * for the current case and governance role.
   */
  const approvalId = useMemo(() => {
    if (!resolvedCase) {
      return "";
    }

    return createApprovalId(
      resolvedCase.case_id,
      role,
    );
  }, [
    resolvedCase?.case_id,
    role,
  ]);

  /*
   * Defensive integration state.
   */
  if (!resolvedCase) {
    return (
      <section className={styles.section}>
        <div
          className={styles.error}
          role="alert"
        >
          Privacy governance case data is unavailable.
        </div>
      </section>
    );
  }

  /*
   * From this point onward TypeScript knows that
   * resolvedCase exists.
   *
   * Create a stable local reference so nested
   * callbacks/functions also retain the narrowing.
   */
  const currentCase =
    resolvedCase;

  const isPending =
    currentCase.governance_status ===
    "PENDING_DPO_GRC";

  /*
   * Completed cases are read-only.
   */
  if (!isPending) {
    return (
      <section className={styles.section}>
        <div
          className={styles.completedCard}
        >
          <div>
            <span
              className={styles.eyebrow}
            >
              HUMAN GOVERNANCE DECISION
            </span>

            <strong>
              Governance decision recorded
            </strong>

            <p>
              This case is currently{" "}
              <b>
                {statusLabel(
                  currentCase.governance_status,
                )}
              </b>
              . No additional decision is
              available while the case is
              outside the pending governance
              state.
            </p>
          </div>
        </div>
      </section>
    );
  }

  const canSubmit =
    reviewer.trim().length > 0 &&
    comment.trim().length > 0 &&
    currentCase.change_id.trim().length > 0 &&
    Boolean(approvalId) &&
    !submitting;

  async function executeDecision(
    decision: GovernanceDecision,
  ): Promise<void> {
    /*
     * Prevent duplicate submissions.
     */
    if (submitting) {
      return;
    }

    /*
     * Validate the authoritative Change ID.
     */
    if (!currentCase.change_id.trim()) {
      setError(
        "This governance case has no linked privacy change. The decision cannot be submitted.",
      );
      return;
    }

    if (!reviewer.trim()) {
      setError(
        "Reviewer identity is required.",
      );
      return;
    }

    if (!comment.trim()) {
      setError(
        "A decision comment is required.",
      );
      return;
    }

    if (!approvalId) {
      setError(
        "Unable to create governance approval evidence identifier.",
      );
      return;
    }

    setSubmitting(true);
    setError(null);

    const request: GovernanceDecisionRequest =
      {
        change_id:
          currentCase.change_id.trim(),

        approval_id:
          approvalId,

        reviewer:
          reviewer.trim(),

        role,

        comment:
          comment.trim(),
      };

    try {
      /*
       * The backend is authoritative.
       */
      const result =
        await submitGovernanceDecision(
          currentCase.case_id,
          decision,
          request,
        );

      /*
       * Only update the parent after successful
       * backend confirmation.
       */
      handleDecisionCompleted?.(
        result.case,
      );

      /*
       * Close confirmation only after success.
       */
      setPendingDecision(null);
      setError(null);
    } catch (cause) {
      /*
       * Keep confirmation workflow open after
       * API failure so the reviewer can retry.
       */
      setError(
        cause instanceof Error
          ? cause.message
          : "Governance decision failed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  function requestDecision(
    decision: GovernanceDecision,
  ): void {
    if (!canSubmit) {
      return;
    }

    setError(null);
    setPendingDecision(decision);
  }

  return (
    <section className={styles.section}>
      <div className={styles.heading}>
        <div>
          <span
            className={styles.eyebrow}
          >
            HUMAN GOVERNANCE DECISION
          </span>

          <h3>
            Decision required
          </h3>

          <p>
            This case passed automated
            validation and is awaiting
            explicit human governance
            approval.
          </p>
        </div>

        <span
          className={styles.pendingBadge}
        >
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
            onChange={(event) => {
              setRole(
                event.target
                  .value as GovernanceRole,
              );

              setPendingDecision(null);
              setError(null);
            }}
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
            onChange={(event) => {
              setReviewer(
                event.target.value,
              );

              if (error) {
                setError(null);
              }
            }}
            placeholder="Enter reviewer name"
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
            onChange={(event) => {
              setComment(
                event.target.value,
              );

              if (error) {
                setError(null);
              }
            }}
            placeholder="Record the rationale for this decision"
            rows={4}
            disabled={submitting}
          />
        </div>

        {!currentCase.change_id.trim() && (
          <div
            className={styles.warning}
            role="alert"
          >
            This case is missing its
            Change ID relationship. A
            governance decision is
            therefore blocked.
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
              requestDecision("approve")
            }
          >
            Approve as {role}
          </button>

          <button
            type="button"
            className={`${styles.actionButton} ${styles.reject}`}
            disabled={!canSubmit}
            onClick={() =>
              requestDecision("reject")
            }
          >
            Reject
          </button>

          <button
            type="button"
            className={`${styles.actionButton} ${styles.changes}`}
            disabled={!canSubmit}
            onClick={() =>
              requestDecision(
                "request-changes",
              )
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
            <span
              className={styles.eyebrow}
            >
              CONFIRM GOVERNANCE DECISION
            </span>

            <h3
              id="governance-confirm-title"
            >
              {decisionLabel(
                pendingDecision,
              )}
            </h3>

            <p>
              You are about to record a
              formal human governance
              decision for:
            </p>

            <dl
              className={
                styles.confirmDetails
              }
            >
              <div>
                <dt>Case</dt>

                <dd>
                  {currentCase.case_id}
                </dd>
              </div>

              <div>
                <dt>Change</dt>

                <dd>
                  {currentCase.change_id}
                </dd>
              </div>

              <div>
                <dt>Role</dt>

                <dd>
                  {role}
                </dd>
              </div>

              <div>
                <dt>Reviewer</dt>

                <dd>
                  {reviewer}
                </dd>
              </div>
            </dl>

            <p
              className={
                styles.confirmWarning
              }
            >
              This action will be recorded
              as governance evidence and
              may change the governance
              state of the case.
            </p>

            <div
              className={
                styles.confirmActions
              }
            >
              <button
                type="button"
                className={
                  styles.cancelButton
                }
                disabled={submitting}
                onClick={() => {
                  setPendingDecision(null);
                  setError(null);
                }}
              >
                Cancel
              </button>

              <button
                type="button"
                className={`${styles.confirmButton} ${
                  pendingDecision ===
                  "approve"
                    ? styles.approve
                    : pendingDecision ===
                        "reject"
                      ? styles.reject
                      : styles.changes
                }`}
                disabled={submitting}
                onClick={() =>
                  void executeDecision(
                    pendingDecision,
                  )
                }
              >
                {submitting
                  ? "Recording..."
                  : "Confirm decision"}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default PrivacyGovernanceDecisionActions;