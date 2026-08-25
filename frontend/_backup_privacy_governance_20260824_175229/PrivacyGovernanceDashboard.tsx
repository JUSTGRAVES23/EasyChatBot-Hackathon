import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getPrivacyGovernanceCase,
  getPrivacyGovernanceCases,
  getPrivacyGovernanceStatusChart,
  getPrivacyGovernanceSummary,
} from "../../lib/privacy-governance/api";

import type {
  PrivacyGovernanceCase,
  PrivacyGovernanceCaseDetail,
  PrivacyGovernanceStatusItem,
  PrivacyGovernanceSummary,
} from "../../lib/privacy-governance/types";

import PrivacyGovernanceCaseDetailComponent from "./PrivacyGovernanceCaseDetail";
import styles from "./PrivacyGovernanceDashboard.module.css";

interface Props {
  initialCaseId?: string | null;
}

type CaseFilter =
  | "ALL"
  | "PENDING_DPO_GRC"
  | "APPROVED"
  | "REJECTED"
  | "BLOCKED";

function statusLabel(
  value?: string | null,
): string {
  if (!value) {
    return "Unknown";
  }

  return value.replaceAll("_", " ");
}

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

function isMatchingFilter(
  caseItem: PrivacyGovernanceCase,
  filter: CaseFilter,
): boolean {
  if (filter === "ALL") {
    return true;
  }

  return (
    caseItem.governance_status === filter
  );
}

function getApprovalHistory(
  caseData: PrivacyGovernanceCase | null,
) {
  if (!caseData) {
    return [];
  }

  return caseData.approval_history ?? [];
}

/**
 * Privacy Governance Dashboard
 *
 * Responsibilities:
 * - Load dashboard summary data.
 * - Load dashboard status distribution.
 * - Load lightweight case register data.
 * - Load authoritative case detail only when a case is opened.
 * - Apply client-side filtering to the case register.
 * - Keep case-detail lifecycle separate from dashboard lifecycle.
 *
 * The component deliberately does not require React Router.
 * This makes the dashboard independently testable and reusable.
 */
export function PrivacyGovernanceDashboard({
  initialCaseId,
}: Props) {
  const [summary, setSummary] =
    useState<PrivacyGovernanceSummary | null>(
      null,
    );

  const [statusChart, setStatusChart] =
    useState<PrivacyGovernanceStatusItem[]>(
      [],
    );

  const [cases, setCases] = useState<
    PrivacyGovernanceCase[]
  >([]);

  const [selectedCaseId, setSelectedCaseId] =
    useState<string | null>(
      initialCaseId ?? null,
    );

  const [selectedCase, setSelectedCase] =
    useState<PrivacyGovernanceCaseDetail | null>(
      null,
    );

  const [
    caseDetailLoading,
    setCaseDetailLoading,
  ] = useState(false);

  const [caseDetailError, setCaseDetailError] =
    useState<string | null>(null);

  const [filter, setFilter] =
    useState<CaseFilter>("ALL");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [refreshing, setRefreshing] =
    useState(false);

  /* ------------------------------------------------------------------------ */
  /* Dashboard loading                                                       */
  /* ------------------------------------------------------------------------ */

  const loadDashboard = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError(null);

      try {
        const [
          summaryResult,
          statusChartResult,
          casesResult,
        ] = await Promise.all([
          getPrivacyGovernanceSummary(),
          getPrivacyGovernanceStatusChart(),
          getPrivacyGovernanceCases(),
        ]);

        setSummary(summaryResult);
        setStatusChart(statusChartResult);
        setCases(casesResult);
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load privacy governance dashboard.",
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [],
  );

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    if (!initialCaseId) {
      return;
    }

    setSelectedCaseId(initialCaseId);
  }, [initialCaseId]);

  /* ------------------------------------------------------------------------ */
  /* Selected case detail                                                     */
  /* ------------------------------------------------------------------------ */

  const loadCaseDetail = useCallback(
    async (caseId: string) => {
      setCaseDetailLoading(true);
      setCaseDetailError(null);
      setSelectedCase(null);

      try {
        const detail =
          await getPrivacyGovernanceCase(
            caseId,
          );

        setSelectedCase(detail);
      } catch (cause) {
        setCaseDetailError(
          cause instanceof Error
            ? cause.message
            : "Unable to load privacy governance case.",
        );
      } finally {
        setCaseDetailLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    if (!selectedCaseId) {
      setSelectedCase(null);
      setCaseDetailError(null);
      setCaseDetailLoading(false);
      return;
    }

    void loadCaseDetail(selectedCaseId);
  }, [
    selectedCaseId,
    loadCaseDetail,
  ]);

  /* ------------------------------------------------------------------------ */
  /* Filtering                                                                */
  /* ------------------------------------------------------------------------ */

  const filteredCases = useMemo(
    () =>
      cases.filter((caseItem) =>
        isMatchingFilter(
          caseItem,
          filter,
        ),
      ),
    [cases, filter],
  );

  const applyFilter = useCallback(
    (nextFilter: CaseFilter) => {
      setFilter((current) =>
        current === nextFilter
          ? "ALL"
          : nextFilter,
      );
    },
    [],
  );

  /* ------------------------------------------------------------------------ */
  /* Case drawer                                                              */
  /* ------------------------------------------------------------------------ */

  const openCase = useCallback(
    (caseId: string) => {
      setSelectedCaseId(caseId);
    },
    [],
  );

  const closeCase = useCallback(() => {
    setSelectedCaseId(null);
    setSelectedCase(null);
    setCaseDetailError(null);
  }, []);

  const retryCaseDetail = useCallback(() => {
    if (!selectedCaseId) {
      return;
    }

    void loadCaseDetail(selectedCaseId);
  }, [
    selectedCaseId,
    loadCaseDetail,
  ]);

  /* ------------------------------------------------------------------------ */
  /* KPI values                                                               */
  /* ------------------------------------------------------------------------ */

  const pendingCount =
    summary?.pending ??
    cases.filter(
      (caseItem) =>
        caseItem.governance_status ===
        "PENDING_DPO_GRC",
    ).length;

  const approvedCount =
    summary?.approved ??
    cases.filter(
      (caseItem) =>
        caseItem.governance_status ===
        "APPROVED",
    ).length;

  const blockedCount =
    summary?.blocked ??
    cases.filter(
      (caseItem) =>
        caseItem.governance_status ===
        "BLOCKED",
    ).length;

  const totalCount =
    summary?.total_cases ??
    cases.length;

  /* ------------------------------------------------------------------------ */
  /* Initial loading                                                          */
  /* ------------------------------------------------------------------------ */

  if (loading && !summary) {
    return (
      <section
        className={styles.dashboard}
        aria-label="Privacy governance dashboard"
      >
        <div
          className={styles.loadingState}
          role="status"
        >
          Loading privacy governance dashboard…
        </div>
      </section>
    );
  }

  return (
    <section
      className={styles.dashboard}
      aria-label="Privacy governance dashboard"
    >
      {/* ------------------------------------------------------------------ */}
      {/* Header                                                             */}
      {/* ------------------------------------------------------------------ */}

      <header className={styles.header}>
        <div>
          <p className={styles.eyebrow}>
            PRIVACY GOVERNANCE
          </p>

          <h1>
            Governance Control Center
          </h1>

          <p className={styles.description}>
            Monitor privacy change governance,
            review approval evidence, and
            record controlled human decisions.
          </p>
        </div>

        <button
          type="button"
          onClick={() =>
            void loadDashboard(true)
          }
          disabled={refreshing}
          className={styles.refreshButton}
        >
          {refreshing
            ? "Refreshing…"
            : "Refresh"}
        </button>
      </header>

      {/* ------------------------------------------------------------------ */}
      {/* Dashboard error                                                     */}
      {/* ------------------------------------------------------------------ */}

      {error && (
        <div
          className={styles.errorState}
          role="alert"
        >
          <strong>
            Unable to load dashboard data.
          </strong>

          <span>{error}</span>

          <button
            type="button"
            onClick={() =>
              void loadDashboard()
            }
          >
            Retry
          </button>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* KPI cards                                                           */}
      {/* ------------------------------------------------------------------ */}

      <section
        className={styles.kpiGrid}
        aria-label="Privacy governance KPIs"
      >
        <button
          type="button"
          className={styles.kpiCard}
          aria-label="Filter all cases"
          onClick={() =>
            applyFilter("ALL")
          }
        >
          <span>Total cases</span>
          <strong>{totalCount}</strong>
        </button>

        <button
          type="button"
          className={styles.kpiCard}
          aria-label="Filter pending DPO/GRC cases"
          onClick={() =>
            applyFilter(
              "PENDING_DPO_GRC",
            )
          }
        >
          <span>Pending DPO/GRC</span>
          <strong>{pendingCount}</strong>
        </button>

        <button
          type="button"
          className={styles.kpiCard}
          aria-label="Filter approved cases"
          onClick={() =>
            applyFilter("APPROVED")
          }
        >
          <span>Approved</span>
          <strong>{approvedCount}</strong>
        </button>

        <button
          type="button"
          className={styles.kpiCard}
          aria-label="Filter blocked cases"
          onClick={() =>
            applyFilter("BLOCKED")
          }
        >
          <span>Blocked</span>
          <strong>{blockedCount}</strong>
        </button>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Status chart                                                        */}
      {/* ------------------------------------------------------------------ */}

      {statusChart.length > 0 && (
        <section
          className={styles.section}
          aria-label="Governance status chart"
        >
          <div
            className={
              styles.sectionHeading
            }
          >
            <div>
              <p
                className={styles.eyebrow}
              >
                STATUS DISTRIBUTION
              </p>

              <h2>
                Governance status
              </h2>
            </div>
          </div>

          <div
            className={styles.statusChart}
          >
            {statusChart.map(
              (status) => (
                <button
                  type="button"
                  key={status.status}
                  className={
                    styles.statusItem
                  }
                  aria-label={`${status.status} ${status.count}`}
                  onClick={() =>
                    applyFilter(
                      status.status as CaseFilter,
                    )
                  }
                >
                  <span>
                    {statusLabel(
                      status.status,
                    )}
                  </span>

                  <strong>
                    {status.count}
                  </strong>
                </button>
              ),
            )}
          </div>
        </section>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Case register                                                       */}
      {/* ------------------------------------------------------------------ */}

      <section
        className={styles.section}
        aria-label="Privacy governance cases"
      >
        <div
          className={styles.sectionHeading}
        >
          <div>
            <p
              className={styles.eyebrow}
            >
              CASE REGISTER
            </p>

            <h2>
              Governance cases
            </h2>
          </div>

          <span>
            {filteredCases.length} case
            {filteredCases.length === 1
              ? ""
              : "s"}
          </span>
        </div>

        {filteredCases.length === 0 ? (
          <div
            className={styles.emptyState}
          >
            No governance cases match the
            selected filter.
          </div>
        ) : (
          <div
            className={styles.caseList}
          >
            {filteredCases.map(
              (caseItem) => (
                <article
                  key={caseItem.case_id}
                  className={
                    styles.caseCard
                  }
                >
                  <div
                    className={
                      styles.caseCardHeader
                    }
                  >
                    <div>
                      <button
                        type="button"
                        className={
                          styles.caseId
                        }
                        aria-label={
                          caseItem.case_id
                        }
                        onClick={() =>
                          openCase(
                            caseItem.case_id,
                          )
                        }
                      >
                        {caseItem.case_id}
                      </button>

                      <h3>
                        {caseItem.title}
                      </h3>
                    </div>

                    <span
                      className={
                        styles.statusBadge
                      }
                    >
                      {statusLabel(
                        caseItem.governance_status,
                      )}
                    </span>
                  </div>

                  <p
                    className={
                      styles.caseSummary
                    }
                  >
                    {caseItem.summary}
                  </p>

                  <dl
                    className={
                      styles.caseMetadata
                    }
                  >
                    <div>
                      <dt>Risk</dt>
                      <dd>
                        {statusLabel(
                          caseItem.risk,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Validation</dt>
                      <dd>
                        {statusLabel(
                          caseItem.validation_status,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Decision</dt>
                      <dd>
                        {statusLabel(
                          caseItem.final_decision,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Updated</dt>
                      <dd>
                        {formatDate(
                          caseItem.final_decision_at,
                        )}
                      </dd>
                    </div>
                  </dl>

                  <div
                    className={
                      styles.caseActions
                    }
                  >
                    <button
                      type="button"
                      aria-label={`View case ${caseItem.case_id}`}
                      onClick={() =>
                        openCase(
                          caseItem.case_id,
                        )
                      }
                    >
                      View case
                    </button>
                  </div>
                </article>
              ),
            )}
          </div>
        )}
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Case detail drawer                                                  */}
      /* ------------------------------------------------------------------ */}

      <PrivacyGovernanceCaseDetailComponent
        open={Boolean(selectedCaseId)}
        loading={caseDetailLoading}
        error={caseDetailError}
        caseData={selectedCase}
        onClose={closeCase}
        onRetry={retryCaseDetail}
        onDecisionComplete={(
          updatedCase,
        ) => {
          setSelectedCase(updatedCase);

          setCases((current) =>
            current.map(
              (caseItem) =>
                caseItem.case_id ===
                updatedCase.case_id
                  ? {
                      ...caseItem,
                      governance_status:
                        updatedCase.governance_status,
                      final_decision:
                        updatedCase.final_decision,
                      final_decision_at:
                        updatedCase.final_decision_at,
                    }
                  : caseItem,
            ),
          );

          setSummary((current) => {
            if (!current) {
              return current;
            }

            return current;
          });
        }}
      />
    </section>
  );
}

export default PrivacyGovernanceDashboard;