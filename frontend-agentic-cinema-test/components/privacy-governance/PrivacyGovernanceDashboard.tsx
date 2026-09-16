import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import PrivacyGovernanceCaseDetail from "./PrivacyGovernanceCaseDetail";
import styles from "./PrivacyGovernanceDashboard.module.css";

import {
  getPrivacyGovernanceCase,
  getPrivacyGovernanceCases,
  getPrivacyGovernanceStatusChart,
  getPrivacyGovernanceSummary,
} from "../../lib/privacy-governance/api";

import type {
  PrivacyGovernanceCase,
  PrivacyGovernanceStatusItem,
  PrivacyGovernanceSummary,
} from "../../lib/privacy-governance/types";

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

function matchesFilter(
  caseItem: PrivacyGovernanceCase,
  filter: CaseFilter,
): boolean {
  if (filter === "ALL") {
    return true;
  }

  return (
    caseItem.governance_status ===
    filter
  );
}

function normalizeStatusChart(
  value: PrivacyGovernanceStatusItem[] | null,
): PrivacyGovernanceStatusItem[] {
  if (!value) {
    return [];
  }

  return value.map((item) => ({
    status: item.status,
    count: Number(item.count ?? 0),
  }));
}

export default function PrivacyGovernanceDashboard({
  initialCaseId = null,
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

  const [filter, setFilter] =
    useState<CaseFilter>("ALL");

  const [selectedCaseId, setSelectedCaseId] =
    useState<string | null>(
      initialCaseId,
    );

  const [selectedCase, setSelectedCase] =
    useState<PrivacyGovernanceCase | null>(
      null,
    );

  const [detailLoading, setDetailLoading] =
    useState(false);

  const [detailError, setDetailError] =
    useState<string | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [refreshing, setRefreshing] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const loadDashboard = useCallback(
    async (
      refresh = false,
    ): Promise<void> => {
      if (refresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError(null);

      try {
        const [
          summaryResult,
          statusResult,
          casesResult,
        ] = await Promise.all([
          getPrivacyGovernanceSummary(),
          getPrivacyGovernanceStatusChart(),
          getPrivacyGovernanceCases(),
        ]);

        setSummary(summaryResult);

        setStatusChart(
          normalizeStatusChart(
            statusResult,
          ),
        );

        setCases(casesResult);
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Backend unavailable.",
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
    setSelectedCaseId(
      initialCaseId ?? null,
    );
  }, [initialCaseId]);

  const loadCaseDetail = useCallback(
    async (
      caseId: string,
    ): Promise<void> => {
      setDetailLoading(true);
      setDetailError(null);

      try {
        const detail =
          await getPrivacyGovernanceCase(
            caseId,
          );

        setSelectedCase(detail);
      } catch (cause) {
        /*
         * Keep the dashboard usable if the
         * detail endpoint fails. The list
         * representation is still useful
         * fallback context.
         */
        const fallback =
          cases.find(
            (caseItem) =>
              caseItem.case_id ===
              caseId,
          ) ?? null;

        setSelectedCase(fallback);

        setDetailError(
          cause instanceof Error
            ? cause.message
            : "Unable to load case detail.",
        );
      } finally {
        setDetailLoading(false);
      }
    },
    [cases],
  );

  useEffect(() => {
    if (!selectedCaseId) {
      setSelectedCase(null);
      setDetailError(null);
      return;
    }

    void loadCaseDetail(
      selectedCaseId,
    );
  }, [
    selectedCaseId,
    loadCaseDetail,
  ]);

  const filteredCases = useMemo(
    () =>
      cases.filter((caseItem) =>
        matchesFilter(
          caseItem,
          filter,
        ),
      ),
    [cases, filter],
  );

  const totalCases =
    summary?.total_cases ??
    cases.length;

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

  const rejectedCount =
    cases.filter(
      (caseItem) =>
        caseItem.governance_status ===
        "REJECTED",
    ).length;

  const rejectedOrBlockedCount =
    rejectedCount +
    blockedCount;

  const approvalRecordCount =
    summary?.approval_records ??
    cases.reduce(
      (total, caseItem) =>
        total +
        (
          caseItem.approval_history ??
          []
        ).length,
      0,
    );

  const applyFilter = useCallback(
    (nextFilter: CaseFilter): void => {
      setFilter((current) =>
        current === nextFilter
          ? "ALL"
          : nextFilter,
      );
    },
    [],
  );

  const filterFromStatus =
    useCallback(
      (status: string): void => {
        const normalized =
          status.toUpperCase();

        if (
          normalized ===
          "PENDING_DPO_GRC"
        ) {
          applyFilter(
            "PENDING_DPO_GRC",
          );
          return;
        }

        if (
          normalized ===
          "APPROVED"
        ) {
          applyFilter("APPROVED");
          return;
        }

        if (
          normalized ===
          "REJECTED"
        ) {
          applyFilter("REJECTED");
          return;
        }

        if (
          normalized ===
          "BLOCKED"
        ) {
          applyFilter("BLOCKED");
        }
      },
      [applyFilter],
    );

  const openCase = useCallback(
    (caseId: string): void => {
      setSelectedCaseId(caseId);
    },
    [],
  );

  const closeCase = useCallback(
    (): void => {
      setSelectedCaseId(null);
      setSelectedCase(null);
      setDetailError(null);
    },
    [],
  );

  const handleDecisionComplete =
    useCallback(
      (
        updatedCase: PrivacyGovernanceCase,
      ): void => {
        setCases((current) =>
          current.map(
            (caseItem) =>
              caseItem.case_id ===
                updatedCase.case_id
                ? updatedCase
                : caseItem,
          ),
        );

        setSelectedCase(
          updatedCase,
        );
      },
      [],
    );

  if (
    loading &&
    !summary &&
    !error
  ) {
    return (
      <main
        className={styles.page}
        aria-label="Privacy governance dashboard"
      >
        <div
          className={styles.emptyState}
          role="status"
        >
          Loading privacy governance dashboard…
        </div>
      </main>
    );
  }

  return (
    <>
      <main
        className={styles.page}
        aria-label="Privacy governance dashboard"
      >
        {/* HEADER */}

        <header
          className={styles.header}
        >
          <div>
            <p
              className={styles.brand}
            >
              EASYCHATBOT · GOVERNANCE
            </p>

            <h1>
              Privacy Governance Center
            </h1>

            <p
              className={styles.subtitle}
            >
              Read-only oversight of
              privacy-impacting changes,
              validation and human
              approval evidence.
            </p>
          </div>

          <button
            type="button"
            className={styles.refresh}
            onClick={() =>
              void loadDashboard(true)
            }
            disabled={refreshing}
          >
            {refreshing
              ? "Refreshing…"
              : "Refresh"}
          </button>
        </header>

        {/* ERROR */}

        {error && (
          <div
            className={
              styles.errorBanner
            }
            role="alert"
          >
            <strong>
              Unable to load governance data.
            </strong>

            <span>
              {error}
            </span>

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

        {/* KPI CARDS */}

        <section
          className={styles.kpis}
          aria-label="Governance KPIs"
        >
          <button
            type="button"
            aria-label="Total cases KPI"
            className={`${styles.kpi} ${filter === "ALL"
                ? styles.kpiActive
                : ""
              }`}
            onClick={() =>
              applyFilter("ALL")
            }
          >
            <span>
              Total cases
            </span>

            <strong>
              {totalCases}
            </strong>
          </button>

          <button
            type="button"
            aria-label="Pending DPO/GRC KPI"
            className={`${styles.kpi} ${filter ===
                "PENDING_DPO_GRC"
                ? styles.kpiActive
                : ""
              }`}
            onClick={() =>
              applyFilter(
                "PENDING_DPO_GRC",
              )
            }
          >
            <span>
              Pending DPO/GRC
            </span>

            <strong>
              {pendingCount}
            </strong>
          </button>

          <button
            type="button"
            aria-label="Approved governance KPI"
            className={`${styles.kpi} ${filter === "APPROVED"
                ? styles.kpiActive
                : ""
              }`}
            onClick={() =>
              applyFilter("APPROVED")
            }
          >
            <span>
              Approved
            </span>

            <strong>
              {approvedCount}
            </strong>
          </button>

          <button
            type="button"
            aria-label="Rejected / blocked KPI"
            className={`${styles.kpi} ${filter === "REJECTED" ||
                filter === "BLOCKED"
                ? styles.kpiActive
                : ""
              }`}
            onClick={() => {
              if (
                rejectedCount >
                0
              ) {
                applyFilter(
                  "REJECTED",
                );
              } else {
                applyFilter(
                  "BLOCKED",
                );
              }
            }}
          >
            <span>
              Rejected / blocked
            </span>

            <strong>
              {
                rejectedOrBlockedCount
              }
            </strong>
          </button>
        </section>

        {/* STATUS */}

        <section
          className={styles.panel}
          aria-label="Governance status"
        >
          <div
            className={
              styles.panelHeader
            }
          >
            <div>
              <p
                className={
                  styles.eyebrow
                }
              >
                OVERSIGHT
              </p>

              <h2>
                Governance status
              </h2>
            </div>

            <span>
              {approvalRecordCount}{" "}
              approval record
              {approvalRecordCount ===
                1
                ? ""
                : "s"}
            </span>
          </div>

          <div
            className={
              styles.statusList
            }
          >
            {statusChart.map(
              (item) => {
                const count =
                  Number(
                    item.count ??
                    0,
                  );

                const percentage =
                  totalCases > 0
                    ? Math.min(
                      100,
                      Math.max(
                        0,
                        (count /
                          totalCases) *
                        100,
                      ),
                    )
                    : 0;

                const label =
                  statusLabel(
                    item.status,
                  );

                /*
                 * IMPORTANT:
                 *
                 * The test contract expects
                 * the status and count to be
                 * present in the accessible
                 * name.
                 *
                 * Example:
                 * "APPROVED 1"
                 *
                 * This does not collide with
                 * the Approved KPI because its
                 * accessible name is
                 * "Approved governance KPI".
                 */
                return (
                  <button
                    type="button"
                    key={
                      item.status
                    }
                    className={
                      styles.statusRow
                    }
                    aria-label={`${label} ${count}`}
                    onClick={() =>
                      filterFromStatus(
                        item.status,
                      )
                    }
                  >
                    <span>
                      {label}
                    </span>

                    <span
                      className={
                        styles.barTrack
                      }
                    >
                      <span
                        className={
                          styles.bar
                        }
                        style={{
                          width: `${percentage}%`,
                        }}
                      />
                    </span>

                    <strong>
                      {count}
                    </strong>
                  </button>
                );
              },
            )}
          </div>
        </section>

        {/* CASE REGISTER */}

        <section
          className={styles.panel}
          aria-label="Privacy governance cases"
        >
          <div
            className={
              styles.panelHeader
            }
          >
            <h2>
              Governance cases
            </h2>

            <div
              className={
                styles.caseMeta
              }
            >
              <span>
                {
                  filteredCases.length
                }{" "}
                case
                {filteredCases.length ===
                  1
                  ? ""
                  : "s"}
              </span>

              {filter !== "ALL" && (
                <button
                  type="button"
                  className={
                    styles.clearFilter
                  }
                  onClick={() =>
                    applyFilter(
                      "ALL",
                    )
                  }
                >
                  Clear filter
                </button>
              )}
            </div>
          </div>

          {filteredCases.length ===
            0 ? (
            <div
              className={
                styles.emptyState
              }
            >
              No governance cases
              match the selected
              filter.
            </div>
          ) : (
            <div
              className={
                styles.tableWrap
              }
            >
              <table
                className={
                  styles.table
                }
              >
                <thead>
                  <tr>
                    <th
                      className={
                        styles.headerCell
                      }
                    >
                      CASE ID
                    </th>

                    <th
                      className={
                        styles.headerCell
                      }
                    >
                      TITLE
                    </th>

                    <th
                      className={
                        styles.headerCell
                      }
                    >
                      STATUS
                    </th>

                    <th
                      className={
                        styles.headerCell
                      }
                    >
                      RISK
                    </th>

                    <th
                      className={
                        styles.headerCell
                      }
                    >
                      VALIDATION
                    </th>

                    <th
                      className={
                        styles.headerCell
                      }
                    >
                      TRIGGER
                    </th>

                    <th
                      className={
                        styles.headerCell
                      }
                    >
                      TRIGGERED
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {filteredCases.map(
                    (caseItem) => (
                      <tr
                        key={
                          caseItem.case_id
                        }
                        className={
                          styles.row
                        }
                      >
                        <td
                          className={
                            styles.cell
                          }
                        >
                          <button
                            type="button"
                            className={
                              styles.caseLink
                            }
                            aria-label={caseItem.case_id}
                            title={`Open case ${caseItem.case_id}`}
                            onClick={() =>
                              openCase(
                                caseItem.case_id,
                              )
                            }
                          >
                            {
                              caseItem.case_id
                            }
                          </button>
                        </td>

                        <td
                          className={
                            styles.cell
                          }
                        >
                          {
                            caseItem.title
                          }
                        </td>

                        <td
                          className={
                            styles.cell
                          }
                        >
                          <span
                            className={
                              styles.statusPill
                            }
                          >
                            {statusLabel(
                              caseItem.governance_status,
                            )}
                          </span>
                        </td>

                        <td
                          className={
                            styles.cell
                          }
                        >
                          {statusLabel(
                            caseItem.risk,
                          )}
                        </td>

                        <td
                          className={
                            styles.cell
                          }
                        >
                          {statusLabel(
                            caseItem.validation_status,
                          )}
                        </td>

                        <td
                          className={
                            styles.cell
                          }
                        >
                          {statusLabel(
                            caseItem.trigger
                              ?.type,
                          )}
                        </td>

                        <td
                          className={
                            styles.cell
                          }
                        >
                          {formatDate(
                            caseItem.trigger
                              ?.at,
                          )}
                        </td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>

      {/* CASE DETAIL */}

      <PrivacyGovernanceCaseDetail
        open={
          selectedCaseId !== null
        }
        loading={detailLoading}
        error={detailError}
        caseData={selectedCase}
        onClose={closeCase}
        onRetry={() => {
          if (
            selectedCaseId
          ) {
            void loadCaseDetail(
              selectedCaseId,
            );
          }
        }}
        onDecisionComplete={
          handleDecisionComplete
        }
      />
    </>
  );
}