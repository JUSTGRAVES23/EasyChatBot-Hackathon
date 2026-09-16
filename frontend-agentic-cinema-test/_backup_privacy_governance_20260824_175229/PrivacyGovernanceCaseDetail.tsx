import type {
  PrivacyGovernanceCaseDetail as PrivacyGovernanceCase,
} from "../../lib/privacy-governance/types";

import PrivacyGovernanceDecisionActions from "./PrivacyGovernanceDecisionActions";
import styles from "./PrivacyGovernanceCaseDetail.module.css";

interface Props {
  open: boolean;
  loading: boolean;
  error: string | null;
  caseData: PrivacyGovernanceCase | null;
  onClose: () => void;
  onRetry: () => void;
  onDecisionComplete: (
    updatedCase: PrivacyGovernanceCase,
  ) => void;
}

type ApprovalRecord = {
  approval_id: string;
  role: string;
  reviewer: string;
  decision?: string | null;
  comment?: string | null;
  decided_at?: string | null;
};

type CaseWithOptionalApprovalRecords =
  PrivacyGovernanceCase & {
    approval_records?: ApprovalRecord[];
  };

function formatDate(
  value?: string | null,
): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function statusLabel(
  value?: string | null,
): string {
  if (!value) {
    return "Not yet decided";
  }

  return value.replaceAll("_", " ");
}

function decisionLabel(
  value?: string | null,
): string {
  if (!value) {
    return "Not yet decided";
  }

  return value.replaceAll("_", " ");
}

export function PrivacyGovernanceCaseDetail({
  open,
  loading,
  error,
  caseData,
  onClose,
  onRetry,
  onDecisionComplete,
}: Props) {
  if (!open) {
    return null;
  }

  /*
   * The backend/test payload may expose approval evidence as
   * either approval_history or approval_records.
   *
   * approval_history remains the primary domain contract.
   * approval_records is supported as a compatibility boundary
   * for existing API/test payloads.
   */
  const caseWithOptionalRecords =
    caseData as
      | CaseWithOptionalApprovalRecords
      | null;

  const approvalHistory =
    caseData?.approval_history ??
    caseWithOptionalRecords?.approval_records ??
    [];

  const processingIds =
    caseData?.processing_ids ?? [];

  const dataMapIds =
    caseData?.data_map_ids ?? [];

  const trigger =
    caseData?.trigger;

  const isPending =
    caseData?.governance_status ===
    "PENDING_DPO_GRC";

  return (
    <div
      className={styles.backdrop}
      role="presentation"
      onMouseDown={onClose}
    >
      <aside
        className={styles.drawer}
        aria-label="Privacy governance case detail"
        onMouseDown={(event) =>
          event.stopPropagation()
        }
      >
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>
              CASE DETAIL
            </p>

            <h2>
              {caseData?.case_id ??
                "Privacy governance case"}
            </h2>
          </div>

          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close case detail"
          >
            ×
          </button>
        </header>

        {loading && (
          <div
            className={styles.state}
            role="status"
          >
            Loading case details…
          </div>
        )}

        {!loading && error && (
          <div
            className={styles.errorState}
            role="alert"
          >
            <strong>
              Unable to load this case.
            </strong>

            <span>{error}</span>

            <button
              type="button"
              onClick={onRetry}
            >
              Retry
            </button>
          </div>
        )}

        {!loading &&
          !error &&
          caseData && (
            <div className={styles.content}>
              {/* -------------------------------------------
                  Governance status
              ------------------------------------------- */}

              <section
                className={styles.summaryCard}
              >
                <span>
                  Governance status
                </span>

                <strong
                  className={styles.status}
                >
                  {statusLabel(
                    caseData.governance_status,
                  )}
                </strong>
              </section>

              {/* -------------------------------------------
                  Case / Change overview
              ------------------------------------------- */}

              <section
                className={styles.section}
              >
                <h3>Overview</h3>

                <dl
                  className={styles.details}
                >
                  <div>
                    <dt>Case ID</dt>
                    <dd>
                      {caseData.case_id}
                    </dd>
                  </div>

                  <div>
                    <dt>Change ID</dt>
                    <dd>
                      {caseData.change_id || "—"}
                    </dd>
                  </div>

                  <div>
                    <dt>Title</dt>
                    <dd>
                      {caseData.title}
                    </dd>
                  </div>

                  <div>
                    <dt>Summary</dt>
                    <dd>
                      {caseData.summary}
                    </dd>
                  </div>

                  <div>
                    <dt>Trigger</dt>
                    <dd>
                      {statusLabel(
                        trigger?.type,
                      )}
                    </dd>
                  </div>

                  <div>
                    <dt>Trigger source</dt>
                    <dd>
                      {trigger?.source || "—"}
                    </dd>
                  </div>

                  <div>
                    <dt>Triggered</dt>
                    <dd>
                      {formatDate(
                        trigger?.at,
                      )}
                    </dd>
                  </div>

                  <div>
                    <dt>Risk</dt>
                    <dd>
                      {statusLabel(
                        caseData.risk,
                      )}
                    </dd>
                  </div>

                  <div>
                    <dt>Validation</dt>
                    <dd>
                      {statusLabel(
                        caseData.validation_status,
                      )}
                    </dd>
                  </div>

                  <div>
                    <dt>Email status</dt>
                    <dd>
                      {statusLabel(
                        caseData.email_status,
                      )}
                    </dd>
                  </div>

                  <div>
                    <dt>Final decision</dt>
                    <dd>
                      {decisionLabel(
                        caseData.final_decision,
                      )}
                    </dd>
                  </div>

                  <div>
                    <dt>Decision time</dt>
                    <dd>
                      {formatDate(
                        caseData.final_decision_at,
                      )}
                    </dd>
                  </div>
                </dl>
              </section>

              {/* -------------------------------------------
                  Privacy scope
              ------------------------------------------- */}

              <section
                className={styles.section}
              >
                <h3>Privacy scope</h3>

                <dl
                  className={styles.details}
                >
                  <div>
                    <dt>Processing IDs</dt>

                    <dd>
                      {processingIds.length > 0
                        ? processingIds.join(", ")
                        : "None recorded"}
                    </dd>
                  </div>

                  <div>
                    <dt>Data mapping IDs</dt>

                    <dd>
                      {dataMapIds.length > 0
                        ? dataMapIds.join(", ")
                        : "None recorded"}
                    </dd>
                  </div>
                </dl>
              </section>

              {/* -------------------------------------------
                  Approval evidence
              ------------------------------------------- */}

              <section
                className={styles.section}
              >
                <div
                  className={
                    styles.sectionHeading
                  }
                >
                  <h3>
                    Approval evidence
                  </h3>

                  <span>
                    {approvalHistory.length}{" "}
                    record
                    {approvalHistory.length === 1
                      ? ""
                      : "s"}
                  </span>
                </div>

                {approvalHistory.length > 0 ? (
                  <div
                    className={styles.approvals}
                  >
                    {approvalHistory.map(
                      (record) => (
                        <article
                          className={
                            styles.approval
                          }
                          key={
                            record.approval_id
                          }
                        >
                          <div
                            className={
                              styles.approvalTop
                            }
                          >
                            <strong>
                              {record.role}
                            </strong>

                            <span>
                              {statusLabel(
                                record.decision,
                              )}
                            </span>
                          </div>

                          <p>
                            {record.reviewer}
                          </p>

                          {record.comment && (
                            <blockquote>
                              {record.comment}
                            </blockquote>
                          )}

                          {record.decided_at && (
                            <small>
                              {formatDate(
                                record.decided_at,
                              )}
                            </small>
                          )}
                        </article>
                      ),
                    )}
                  </div>
                ) : (
                  <p
                    className={
                      styles.empty
                    }
                  >
                    No approval evidence has
                    been recorded for this case.
                  </p>
                )}
              </section>

              {/* -------------------------------------------
                  Human governance decision
              ------------------------------------------- */}

              {isPending && (
                <PrivacyGovernanceDecisionActions
                  caseData={caseData}
                  onDecisionComplete={
                    onDecisionComplete
                  }
                />
              )}
            </div>
          )}
      </aside>
    </div>
  );
}

export default PrivacyGovernanceCaseDetail;