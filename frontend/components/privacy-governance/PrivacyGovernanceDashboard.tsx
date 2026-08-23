import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getPrivacyGovernanceCase,
  loadPrivacyGovernanceDashboard,
} from "../../lib/privacy-governance/api";
import type {
  GovernanceFilter,
  PrivacyGovernanceCase,
  PrivacyGovernanceStatusItem,
  PrivacyGovernanceSummary,
} from "../../lib/privacy-governance/types";
import PrivacyGovernanceCaseDetail from "./PrivacyGovernanceCaseDetail";
import styles from "./PrivacyGovernanceDashboard.module.css";

const EMPTY_SUMMARY: PrivacyGovernanceSummary = {
  total_cases: 0,
  pending: 0,
  approved: 0,
  blocked: 0,
  approval_records: 0,
};

interface Props {
  initialLoad?: boolean;

  /**
   * Optional case ID supplied by the privacy-governance
   * deep-link route:
   *
   * /privacy-governance/:caseId
   *
   * This is intentionally dynamic. No case ID is hard-coded.
   */
  initialCaseId?: string;
}

function normalizeStatus(status: string): GovernanceFilter {
  const value = status.toUpperCase();

  if (value.includes("PENDING")) {
    return "PENDING_DPO_GRC";
  }

  if (value.includes("APPROVED")) {
    return "APPROVED";
  }

  if (
    value.includes("BLOCKED") ||
    value.includes("REJECTED")
  ) {
    return "BLOCKED";
  }

  return "ALL";
}

function statusLabel(value?: string | null): string {
  if (!value) {
    return "Unknown";
  }

  return value.replaceAll("_", " ");
}

function formatDate(value?: string | null): string {
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

export function PrivacyGovernanceDashboard({
  initialLoad = true,
  initialCaseId,
}: Props) {
  const [summary, setSummary] =
    useState<PrivacyGovernanceSummary>(
      EMPTY_SUMMARY,
    );

  const [statusChart, setStatusChart] =
    useState<PrivacyGovernanceStatusItem[]>([]);

  const [cases, setCases] =
    useState<PrivacyGovernanceCase[]>([]);

  const [filter, setFilter] =
    useState<GovernanceFilter>("ALL");

  const [loading, setLoading] =
    useState(initialLoad);

  const [refreshing, setRefreshing] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [selectedCaseId, setSelectedCaseId] =
    useState<string | null>(null);

  const [selectedCase, setSelectedCase] =
    useState<PrivacyGovernanceCase | null>(null);

  const [detailLoading, setDetailLoading] =
    useState(false);

  const [detailError, setDetailError] =
    useState<string | null>(null);

  /*
   * ---------------------------------------------------------
   * Dashboard data
   * ---------------------------------------------------------
   */

  const loadDashboard = useCallback(
    async (
      mode: "initial" | "refresh" = "refresh",
    ) => {
      if (mode === "initial") {
        setLoading(true);
      } else {
        setRefreshing(true);
      }

      setError(null);

      try {
        const result =
          await loadPrivacyGovernanceDashboard();

        setSummary(result.summary);
        setStatusChart(result.statusChart);
        setCases(result.cases);
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load privacy governance data.",
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [],
  );

  useEffect(() => {
    if (initialLoad) {
      void loadDashboard("initial");
    }
  }, [initialLoad, loadDashboard]);

  /*
   * ---------------------------------------------------------
   * Case filtering
   * ---------------------------------------------------------
   */

  const visibleCases = useMemo(() => {
    if (filter === "ALL") {
      return cases;
    }

    return cases.filter(
      (item) =>
        normalizeStatus(
          item.governance_status,
        ) === filter,
    );
  }, [cases, filter]);

  /*
   * ---------------------------------------------------------
   * Case detail
   * ---------------------------------------------------------
   */

  const openCase = useCallback(
    async (caseId: string) => {
      const normalizedCaseId = caseId.trim();

      if (!normalizedCaseId) {
        setSelectedCaseId(null);
        setSelectedCase(null);
        setDetailError(
          "A valid governance case ID is required.",
        );
        return;
      }

      setSelectedCaseId(normalizedCaseId);
      setSelectedCase(null);
      setDetailError(null);
      setDetailLoading(true);

      try {
        const detail =
          await getPrivacyGovernanceCase(
            normalizedCaseId,
          );

        setSelectedCase(detail);
      } catch (cause) {
        setDetailError(
          cause instanceof Error
            ? cause.message
            : "Unable to load this governance case.",
        );
      } finally {
        setDetailLoading(false);
      }
    },
    [],
  );

  /*
   * ---------------------------------------------------------
   * Privacy Governance Email Deep Link
   *
   * /privacy-governance/<actual-case-id>
   *
   * No case ID is hard-coded.
   * ---------------------------------------------------------
   */

  useEffect(() => {
    const caseId = initialCaseId?.trim();

    if (!caseId) {
      return;
    }

    void openCase(caseId);
  }, [initialCaseId, openCase]);

  const retryCase = useCallback(() => {
    if (selectedCaseId) {
      void openCase(selectedCaseId);
    }
  }, [openCase, selectedCaseId]);

  /*
   * ---------------------------------------------------------
   * Decision completed
   * ---------------------------------------------------------
   */

  const handleDecisionComplete = useCallback(
    (updatedCase: PrivacyGovernanceCase) => {
      setSelectedCase(updatedCase);

      setCases((current) =>
        current.map((item) =>
          item.case_id === updatedCase.case_id
            ? updatedCase
            : item,
        ),
      );

      void loadDashboard("refresh");
    },
    [loadDashboard],
  );

  /*
   * ---------------------------------------------------------
   * Status filtering
   * ---------------------------------------------------------
   */

  const filterFromStatus = useCallback(
    (status: string) => {
      setFilter(normalizeStatus(status));
    },
    [],
  );

  /*
   * ---------------------------------------------------------
   * KPI configuration
   * ---------------------------------------------------------
   */

  const kpis: Array<{
    label: string;
    value: number;
    filter: GovernanceFilter;
  }> = [
    {
      label: "Total cases",
      value: summary.total_cases,
      filter: "ALL",
    },
    {
      label: "Pending DPO/GRC",
      value: summary.pending,
      filter: "PENDING_DPO_GRC",
    },
    {
      label: "Approved",
      value: summary.approved,
      filter: "APPROVED",
    },
    {
      label: "Rejected / blocked",
      value: summary.blocked,
      filter: "BLOCKED",
    },
  ];

  /*
   * ---------------------------------------------------------
   * Render
   * ---------------------------------------------------------
   */

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <p className={styles.brand}>
            EASYCHATBOT · GOVERNANCE
          </p>

          <h1>
            Privacy Governance Center
          </h1>

          <p className={styles.subtitle}>
            Read-only oversight of privacy-impacting
            changes, validation and human approval
            evidence.
          </p>
        </div>

        <button
          type="button"
          className={styles.refresh}
          onClick={() =>
            void loadDashboard("refresh")
          }
          disabled={refreshing}
        >
          {refreshing
            ? "Refreshing…"
            : "Refresh"}
        </button>
      </header>

      {error && (
        <section
          className={styles.errorBanner}
          role="alert"
        >
          <div>
            <strong>
              Unable to load governance data.
            </strong>

            <span>{error}</span>
          </div>

          <button
            type="button"
            onClick={() =>
              void loadDashboard("refresh")
            }
          >
            Retry
          </button>
        </section>
      )}

      <section
        className={styles.kpis}
        aria-label="Governance KPIs"
      >
        {kpis.map((kpi) => (
          <button
            type="button"
            key={kpi.label}
            className={`${styles.kpi} ${
              filter === kpi.filter
                ? styles.kpiActive
                : ""
            }`}
            onClick={() =>
              setFilter(kpi.filter)
            }
          >
            <span>{kpi.label}</span>

            <strong>
              {loading
                ? "…"
                : kpi.value}
            </strong>
          </button>
        ))}
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <p className={styles.eyebrow}>
              OVERSIGHT
            </p>

            <h2>
              Governance status
            </h2>
          </div>

          <span>
            {loading
              ? "Loading…"
              : `${summary.approval_records} approval records`}
          </span>
        </div>

        <div className={styles.statusList}>
          {statusChart.length ? (
            statusChart.map((item) => {
              const maximum = Math.max(
                1,
                ...statusChart.map(
                  (entry) => entry.count,
                ),
              );

              return (
                <button
                  type="button"
                  className={`${styles.statusRow} ${
                    filter ===
                    normalizeStatus(
                      item.status,
                    )
                      ? styles.statusActive
                      : ""
                  }`}
                  key={item.status}
                  onClick={() =>
                    filterFromStatus(
                      item.status,
                    )
                  }
                >
                  <span>
                    {statusLabel(
                      item.status,
                    )}
                  </span>

                  <span
                    className={
                      styles.barTrack
                    }
                  >
                    <span
                      className={styles.bar}
                      style={{
                        width: `${
                          (item.count /
                            maximum) *
                          100
                        }%`,
                      }}
                    />
                  </span>

                  <strong>
                    {item.count}
                  </strong>
                </button>
              );
            })
          ) : (
            <div
              className={
                styles.emptyState
              }
            >
              No governance status data.
            </div>
          )}
        </div>
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <p className={styles.eyebrow}>
              CASE REGISTER
            </p>

            <h2>
              Privacy governance cases
            </h2>
          </div>

          <div
            className={
              styles.caseMeta
            }
          >
            {filter !== "ALL" && (
              <button
                type="button"
                className={
                  styles.clearFilter
                }
                onClick={() =>
                  setFilter("ALL")
                }
              >
                {statusLabel(filter)} ×
              </button>
            )}

            <span>
              {loading
                ? "Loading…"
                : `${visibleCases.length} cases`}
            </span>
          </div>
        </div>

        <div
          className={styles.tableWrap}
        >
          <table>
            <thead>
              <tr>
                <th>CASE</th>
                <th>TRIGGER</th>
                <th>TRIGGERED</th>
                <th>RISK</th>
                <th>VALIDATION</th>
                <th>STATUS</th>
              </tr>
            </thead>

            <tbody>
              {!loading &&
                visibleCases.map(
                  (item) => (
                    <tr
                      key={item.case_id}
                    >
                      <td>
                        <button
                          type="button"
                          className={
                            styles.caseLink
                          }
                          onClick={() =>
                            void openCase(
                              item.case_id,
                            )
                          }
                          aria-label={`Open case ${item.case_id}`}
                        >
                          {item.case_id}
                        </button>
                      </td>

                      <td>
                        {statusLabel(
                          item.trigger?.type,
                        )}
                      </td>

                      <td>
                        {formatDate(
                          item.trigger?.at,
                        )}
                      </td>

                      <td>
                        {item.risk ?? "—"}
                      </td>

                      <td>
                        {statusLabel(
                          item.validation_status,
                        )}
                      </td>

                      <td>
                        <span
                          className={
                            styles.statusPill
                          }
                        >
                          {statusLabel(
                            item.governance_status,
                          )}
                        </span>
                      </td>
                    </tr>
                  ),
                )}
            </tbody>
          </table>

          {loading && (
            <div
              className={
                styles.emptyState
              }
              role="status"
            >
              Loading governance cases…
            </div>
          )}

          {!loading &&
            !visibleCases.length && (
              <div
                className={
                  styles.emptyState
                }
              >
                {filter === "ALL"
                  ? "No governance cases are currently registered."
                  : "No cases match the selected filter."}
              </div>
            )}
        </div>
      </section>

      <PrivacyGovernanceCaseDetail
        open={Boolean(
          selectedCaseId,
        )}
        loading={detailLoading}
        error={detailError}
        caseData={selectedCase}
        onClose={() => {
          setSelectedCaseId(null);
          setSelectedCase(null);
          setDetailError(null);
        }}
        onRetry={retryCase}
        onDecisionComplete={
          handleDecisionComplete
        }
      />
    </main>
  );
}

export default PrivacyGovernanceDashboard;