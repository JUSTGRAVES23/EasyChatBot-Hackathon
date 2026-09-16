"use client";

import { useCallback, useEffect, useState } from "react";
import styles from "../PersistenceOperations.module.css";
import type {
  Environment,
  HealthSnapshot,
} from "../types";

/*
 * EasyChatBot frontend is Vite.
 *
 * API requests intentionally use the relative /api path.
 * Vite proxies /api to the FastAPI backend.
 *
 * Do NOT use process.env.NEXT_PUBLIC_* in browser code.
 */
const API_BASE = "";

const environments: Array<{
  value: Environment;
  label: string;
}> = [
  {
    value: "dev",
    label: "Development (DEV)",
  },
  {
    value: "staging",
    label: "Staging",
  },
  {
    value: "production",
    label: "Production",
  },
];

function format(value: unknown): string {
  if (value == null || value === "") {
    return "Not available";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  return String(value);
}

function date(value: unknown): string {
  if (!value) return "—";

  const parsed = new Date(String(value));

  return Number.isNaN(parsed.getTime())
    ? String(value)
    : parsed.toLocaleString();
}

function tone(value: string): string {
  if (
    [
      "HEALTHY",
      "OK",
      "IN_SYNC",
      "CONNECTED",
      "on",
    ].includes(value)
  ) {
    return styles.good;
  }

  if (
    [
      "NOT_CONFIGURED",
      "NOT_AVAILABLE",
      "UNKNOWN",
    ].includes(value)
  ) {
    return styles.warn;
  }

  return styles.bad;
}

export default function DatabaseHealthOperationsPage() {
  const [environment, setEnvironment] =
    useState<Environment>("dev");

  const [snapshot, setSnapshot] =
    useState<HealthSnapshot | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [notice, setNotice] =
    useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    setNotice(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/operations-center/persistence/health?environment=${environment}`,
        {
          cache: "no-store",
        },
      );

      if (!response.ok) {
        throw new Error(
          `Persistence health API returned HTTP ${response.status}.`,
        );
      }

      setSnapshot(
        (await response.json()) as HealthSnapshot,
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load database health diagnostics.",
      );
    } finally {
      setLoading(false);
    }
  }, [environment]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <main className={styles.shell}>
      <header className={styles.topbar}>
        <div className={styles.brand}>
          <div className={styles.brandMark}>
            <span>✦</span>
          </div>

          <div>
            <strong>EASYWORLD</strong>
            <small>
              ACADEMY · A MORE HUMAN FUTURE. TOGETHER.
            </small>
          </div>
        </div>

        <div className={styles.topbarRight}>
          <span className={styles.brandMotto}>
            Knowledge turns potential into impact.
          </span>

          <span className={styles.liveBadge}>
            <i /> Live diagnostics
          </span>

          <label
            className={styles.environmentSelect}
          >
            <span>Environment</span>

            <select
              value={environment}
              onChange={(event) =>
                setEnvironment(
                  event.target.value as Environment,
                )
              }
            >
              {environments.map((item) => (
                <option
                  key={item.value}
                  value={item.value}
                >
                  {item.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>

      <div className={styles.layout}>
        <aside className={styles.sidebar}>
          <div className={styles.sideSectionLabel}>
            OPERATIONS CENTER
          </div>

          <nav
            className={styles.sideNav}
            aria-label="Operations Center"
          >
            <a
              href="/operations-center"
              className={styles.navItem}
            >
              <span>⌂</span>
              <span>Overview</span>
            </a>

            <a
              href="/operations-center/functionality-health"
              className={styles.navItem}
            >
              <span>⌁</span>
              <span>Functionality Health</span>
            </a>

            <a
              href="/operations-center/persistence"
              className={`${styles.navItem} ${styles.active}`}
            >
              <span>▤</span>
              <span>Persistence Control</span>
            </a>

            <a
              href="/project-control"
              className={styles.navItem}
            >
              <span>▣</span>
              <span>Project Control</span>
            </a>

            <a
              href="/operations-center/agents"
              className={styles.navItem}
            >
              <span>♙</span>
              <span>Agents</span>
            </a>

            <span
              className={`${styles.navItem} ${styles.navDisabled}`}
            >
              <span>◇</span>
              <span>Quality Management</span>
            </span>

            <span
              className={`${styles.navItem} ${styles.navDisabled}`}
            >
              <span>◈</span>
              <span>Security &amp; Governance</span>
            </span>

            <span
              className={`${styles.navItem} ${styles.navDisabled}`}
            >
              <span>▥</span>
              <span>Monitoring</span>
            </span>

            <span
              className={`${styles.navItem} ${styles.navDisabled}`}
            >
              <span>☷</span>
              <span>Logs</span>
            </span>

            <span
              className={`${styles.navItem} ${styles.navDisabled}`}
            >
              <span>⚙</span>
              <span>Configuration</span>
            </span>
          </nav>

          <div className={styles.sideBottom}>
            <label
              className={styles.environmentSelect}
            >
              <span>Environment</span>

              <select
                value={environment}
                onChange={(event) =>
                  setEnvironment(
                    event.target.value as Environment,
                  )
                }
              >
                {environments.map((item) => (
                  <option
                    key={item.value}
                    value={item.value}
                  >
                    {item.label}
                  </option>
                ))}
              </select>
            </label>

            <div className={styles.helpCard}>
              <div className={styles.helpIcon}>?</div>

              <div>
                <strong>Need help?</strong>

                <span>
                  Operational facts are live;
                  unavailable integrations are never
                  fabricated.
                </span>
              </div>
            </div>
          </div>
        </aside>

        <section className={styles.content}>
          <div className={styles.breadcrumb}>
            <a href="/operations-center">
              Operations Center
            </a>

            <span>›</span>

            <a href="/operations-center/persistence">
              Persistence Operations
            </a>

            <span>›</span>

            <span>
              Database Health &amp; Operations
            </span>
          </div>

          <header className={styles.pageHeader}>
            <div>
              <div className={styles.kicker}>
                POSTGRESQL DIAGNOSTICS ·{" "}
                {environment.toUpperCase()}
              </div>

              <h1>Database Health &amp; Operations</h1>

              <p>
                Deep PostgreSQL diagnostics for
                performance, locks, maintenance,
                recovery and security.
              </p>
            </div>

            <div className={styles.headerMeta}>
              <span>
                Last updated
                <br />

                <strong>
                  {snapshot
                    ? date(snapshot.checked_at)
                    : "—"}
                </strong>
              </span>

              <button
                className={styles.secondaryButton}
                onClick={() => void refresh()}
                disabled={loading}
              >
                ↻ Refresh
              </button>
            </div>
          </header>

          <nav
            className={styles.tabs}
            aria-label="Database health sections"
          >
            <a href="/operations-center/persistence">
              Overview
            </a>

            <span className={styles.tabActive}>
              Database Health &amp; Operations
            </span>

            <a href="#performance">
              Performance
            </a>

            <a href="#locks">
              Locks &amp; Activity
            </a>

            <a href="#recovery">
              Backups &amp; Recovery
            </a>

            <a href="#security">
              Security
            </a>
          </nav>

          {loading && !snapshot ? (
            <div className={styles.notice}>
              <span className={styles.spinner} />
              Loading live PostgreSQL diagnostics…
            </div>
          ) : null}

          {error ? (
            <div
              className={`${styles.notice} ${styles.errorNotice}`}
              role="alert"
            >
              <strong>
                Database diagnostics unavailable.
              </strong>

              <span>{error}</span>

              <button
                onClick={() => void refresh()}
              >
                Retry
              </button>
            </div>
          ) : null}

          {snapshot ? (
            <>
              <section
                className={`${styles.healthBanner} ${
                  snapshot.database.connected
                    ? ""
                    : styles.healthBad
                }`}
              >
                <span className={styles.healthIcon}>
                  {snapshot.database.connected
                    ? "✓"
                    : "!"}
                </span>

                <div>
                  <strong>
                    {snapshot.database.connected
                      ? "Database is reachable"
                      : snapshot.status ===
                          "NOT_CONFIGURED"
                        ? "Environment not configured"
                        : "Database unavailable"}
                  </strong>

                  <p>
                    {snapshot.database
                      .postgres_version ??
                      snapshot.error ??
                      "PostgreSQL status unavailable"}{" "}
                    ·{" "}
                    {snapshot.database.database ??
                      "—"}
                  </p>
                </div>

                <span
                  className={tone(snapshot.status)}
                >
                  {snapshot.status}
                </span>
              </section>

              <section className={styles.healthGrid}>
                <article className={styles.panel}>
                  <div
                    className={styles.panelHeader}
                  >
                    <div>
                      <span
                        className={styles.kicker}
                      >
                        CONNECTION
                      </span>

                      <h2>
                        Connection &amp; Capacity
                      </h2>
                    </div>

                    <span>
                      {snapshot.database
                        .connection_utilisation_pct ==
                      null
                        ? "—"
                        : `${snapshot.database.connection_utilisation_pct}%`}
                    </span>
                  </div>

                  <dl className={styles.details}>
                    <div>
                      <dt>Host</dt>
                      <dd>
                        {format(
                          snapshot.database.host,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Port</dt>
                      <dd>
                        {format(
                          snapshot.database.port,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>PostgreSQL</dt>
                      <dd>
                        {format(
                          snapshot.database
                            .postgres_version,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Database</dt>
                      <dd>
                        {format(
                          snapshot.database.database,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Connections</dt>
                      <dd>
                        {format(
                          snapshot.database
                            .active_connections,
                        )}{" "}
                        /{" "}
                        {format(
                          snapshot.database
                            .max_connections,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Latency</dt>
                      <dd>
                        {snapshot.database
                          .latency_ms == null
                          ? "—"
                          : `${snapshot.database.latency_ms} ms`}
                      </dd>
                    </div>

                    <div>
                      <dt>Uptime</dt>
                      <dd>
                        {format(
                          snapshot.database.uptime,
                        )}
                      </dd>
                    </div>
                  </dl>
                </article>

                <article
                  id="performance"
                  className={styles.panel}
                >
                  <div
                    className={styles.panelHeader}
                  >
                    <div>
                      <span
                        className={styles.kicker}
                      >
                        QUERY HEALTH
                      </span>

                      <h2>Performance</h2>
                    </div>

                    <span>
                      {
                        snapshot.performance
                          .query_statistics
                      }
                    </span>
                  </div>

                  <div className={styles.statGrid}>
                    <div>
                      <small>Cache hit</small>

                      <strong>
                        {snapshot.performance
                          .cache_hit_ratio_pct ==
                        null
                          ? "—"
                          : `${snapshot.performance.cache_hit_ratio_pct}%`}
                      </strong>
                    </div>

                    <div>
                      <small>Committed</small>

                      <strong>
                        {format(
                          snapshot.performance
                            .transactions_committed,
                        )}
                      </strong>
                    </div>

                    <div>
                      <small>Rolled back</small>

                      <strong>
                        {format(
                          snapshot.performance
                            .transactions_rolled_back,
                        )}
                      </strong>
                    </div>

                    <div>
                      <small>Rows returned</small>

                      <strong>
                        {format(
                          snapshot.performance
                            .rows_returned,
                        )}
                      </strong>
                    </div>
                  </div>

                  <h3>Slow queries</h3>

                  {snapshot.performance.slow_queries
                    .length ? (
                    <div
                      className={
                        styles.compactList
                      }
                    >
                      {snapshot.performance.slow_queries.map(
                        (row) => (
                          <div
                            key={`${row.query}-${row.calls}`}
                          >
                            <span title={row.query}>
                              {row.query}
                            </span>

                            <strong>
                              {row.mean_ms} ms
                            </strong>
                          </div>
                        ),
                      )}
                    </div>
                  ) : (
                    <p className={styles.muted}>
                      Query-level statistics are
                      unavailable because
                      pg_stat_statements is not enabled
                      or not accessible.
                    </p>
                  )}
                </article>

                <article
                  id="locks"
                  className={styles.panel}
                >
                  <div
                    className={styles.panelHeader}
                  >
                    <div>
                      <span
                        className={styles.kicker}
                      >
                        CONCURRENCY
                      </span>

                      <h2>
                        Locks &amp; Blocking
                      </h2>
                    </div>

                    <span
                      className={
                        snapshot.locks
                          .blocking_detected
                          ? styles.bad
                          : styles.good
                      }
                    >
                      {snapshot.locks
                        .blocking_detected
                        ? "Blocking detected"
                        : "No blocking"}
                    </span>
                  </div>

                  <p className={styles.muted}>
                    {snapshot.locks.blocking_detected
                      ? `${snapshot.locks.blocked_queries.length} blocked query(ies) detected.`
                      : "No currently blocked queries detected."}
                  </p>

                  <div className={styles.statGrid}>
                    <div>
                      <small>
                        Active transactions
                      </small>

                      <strong>
                        {format(
                          snapshot.locks
                            .active_transactions,
                        )}
                      </strong>
                    </div>

                    <div>
                      <small>Long-running</small>

                      <strong>
                        {
                          snapshot.locks
                            .long_running_transactions
                            .length
                        }
                      </strong>
                    </div>

                    <div>
                      <small>Blocked</small>

                      <strong>
                        {
                          snapshot.locks
                            .blocked_queries.length
                        }
                      </strong>
                    </div>
                  </div>

                  <h3>
                    Long-running transactions
                  </h3>

                  {snapshot.locks
                    .long_running_transactions.length ? (
                    <div
                      className={
                        styles.compactList
                      }
                    >
                      {snapshot.locks.long_running_transactions
                        .slice(0, 5)
                        .map((row, index) => (
                          <div
                            key={`${row.pid}-${index}`}
                          >
                            <span
                              title={format(
                                row.query,
                              )}
                            >
                              {format(row.query)}
                            </span>

                            <strong>
                              {format(
                                row.transaction_age,
                              )}
                            </strong>
                          </div>
                        ))}
                    </div>
                  ) : (
                    <p className={styles.muted}>
                      No transaction older than the
                      diagnostic threshold was detected.
                    </p>
                  )}
                </article>

                <article className={styles.panel}>
                  <div
                    className={styles.panelHeader}
                  >
                    <div>
                      <span
                        className={styles.kicker}
                      >
                        INDEXES
                      </span>

                      <h2>Index Health</h2>
                    </div>

                    <span>
                      {format(
                        snapshot.indexes
                          .total_indexes,
                      )}{" "}
                      inspected
                    </span>
                  </div>

                  <div className={styles.statGrid}>
                    <div>
                      <small>Total indexes</small>

                      <strong>
                        {format(
                          snapshot.indexes
                            .total_indexes,
                        )}
                      </strong>
                    </div>

                    <div>
                      <small>Unused</small>

                      <strong
                        className={
                          snapshot.indexes
                            .unused_index_count
                            ? styles.warn
                            : styles.good
                        }
                      >
                        {format(
                          snapshot.indexes
                            .unused_index_count,
                        )}
                      </strong>
                    </div>

                    <div>
                      <small>Invalid</small>

                      <strong
                        className={
                          snapshot.indexes
                            .invalid_indexes
                            ? styles.bad
                            : styles.good
                        }
                      >
                        {format(
                          snapshot.indexes
                            .invalid_indexes,
                        )}
                      </strong>
                    </div>
                  </div>

                  <p className={styles.muted}>
                    Unused indexes are candidates for
                    review, not automatic deletion.
                  </p>
                </article>

                <article className={styles.panel}>
                  <div
                    className={styles.panelHeader}
                  >
                    <div>
                      <span
                        className={styles.kicker}
                      >
                        MAINTENANCE
                      </span>

                      <h2>Maintenance</h2>
                    </div>

                    <span
                      className={tone(
                        snapshot.maintenance
                          .autovacuum ??
                          "UNKNOWN",
                      )}
                    >
                      {format(
                        snapshot.maintenance
                          .autovacuum,
                      )}
                    </span>
                  </div>

                  <dl className={styles.details}>
                    <div>
                      <dt>Tables inspected</dt>

                      <dd>
                        {
                          snapshot.maintenance
                            .tables.length
                        }
                      </dd>
                    </div>

                    <div>
                      <dt>
                        Tables with dead tuples
                      </dt>

                      <dd>
                        {format(
                          snapshot.maintenance
                            .tables_with_dead_tuples,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Autovacuum</dt>

                      <dd>
                        {format(
                          snapshot.maintenance
                            .autovacuum,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Track counts</dt>

                      <dd>
                        {format(
                          snapshot.maintenance
                            .track_counts,
                        )}
                      </dd>
                    </div>
                  </dl>

                  <p className={styles.muted}>
                    Detailed vacuum/analyze timestamps
                    are available from PostgreSQL table
                    statistics.
                  </p>
                </article>

                <article
                  id="recovery"
                  className={styles.panel}
                >
                  <div
                    className={styles.panelHeader}
                  >
                    <div>
                      <span
                        className={styles.kicker}
                      >
                        RECOVERY
                      </span>

                      <h2>
                        Backup &amp; Recovery
                      </h2>
                    </div>

                    <span>
                      {
                        snapshot.backup_recovery
                          .backup_integration
                      }
                    </span>
                  </div>

                  <dl className={styles.details}>
                    <div>
                      <dt>Last backup</dt>
                      <dd>
                        {format(
                          snapshot.backup_recovery
                            .last_backup,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Backup status</dt>
                      <dd>
                        {format(
                          snapshot.backup_recovery
                            .backup_status,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>
                        Restore verification
                      </dt>
                      <dd>
                        {format(
                          snapshot.backup_recovery
                            .restore_verification,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>
                        Point-in-time recovery
                      </dt>
                      <dd>
                        {format(
                          snapshot.backup_recovery
                            .point_in_time_recovery,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Archive mode</dt>
                      <dd>
                        {format(
                          snapshot.backup_recovery
                            .archive_mode,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>WAL level</dt>
                      <dd>
                        {format(
                          snapshot.backup_recovery
                            .wal_level,
                        )}
                      </dd>
                    </div>
                  </dl>

                  <p className={styles.muted}>
                    Backup and restore values are never
                    invented. Connect the approved backup
                    provider to expose operational
                    evidence.
                  </p>
                </article>

                <article className={styles.panel}>
                  <div
                    className={styles.panelHeader}
                  >
                    <div>
                      <span
                        className={styles.kicker}
                      >
                        INTEGRITY
                      </span>

                      <h2>Data Integrity</h2>
                    </div>

                    <span>
                      {
                        snapshot.integrity
                          .application_integrity_checks
                      }
                    </span>
                  </div>

                  <div className={styles.statGrid}>
                    <div>
                      <small>Foreign keys</small>

                      <strong>
                        {format(
                          snapshot.integrity
                            .foreign_key_constraints,
                        )}
                      </strong>
                    </div>

                    <div>
                      <small>
                        Check constraints
                      </small>

                      <strong>
                        {format(
                          snapshot.integrity
                            .check_constraints,
                        )}
                      </strong>
                    </div>
                  </div>

                  <p className={styles.muted}>
                    Application-specific orphan,
                    duplicate and business-key checks
                    require an explicit integrity-check
                    registry.
                  </p>
                </article>

                <article
                  id="security"
                  className={styles.panel}
                >
                  <div
                    className={styles.panelHeader}
                  >
                    <div>
                      <span
                        className={styles.kicker}
                      >
                        ACCESS CONTROL
                      </span>

                      <h2>
                        Security &amp; Access
                      </h2>
                    </div>

                    <span>
                      {snapshot.security
                        .current_role ?? "—"}
                    </span>
                  </div>

                  <dl className={styles.details}>
                    <div>
                      <dt>SSL</dt>
                      <dd>
                        {format(
                          snapshot.security
                            .ssl_enabled,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Superuser</dt>
                      <dd>
                        {format(
                          snapshot.security
                            .is_superuser,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Create role</dt>
                      <dd>
                        {format(
                          snapshot.security
                            .can_create_role,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Create database</dt>
                      <dd>
                        {format(
                          snapshot.security
                            .can_create_database,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Can login</dt>
                      <dd>
                        {format(
                          snapshot.security.can_login,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>pg_hba analysis</dt>
                      <dd>
                        {format(
                          snapshot.security
                            .pg_hba_analysis,
                        )}
                      </dd>
                    </div>
                  </dl>
                </article>

                <article className={styles.panel}>
                  <div
                    className={styles.panelHeader}
                  >
                    <div>
                      <span
                        className={styles.kicker}
                      >
                        WAL
                      </span>

                      <h2>
                        WAL &amp; Replication
                      </h2>
                    </div>

                    <span>
                      {snapshot.replication
                        .is_standby == null
                        ? "Unknown"
                        : snapshot.replication
                              .is_standby
                          ? "Standby"
                          : "Primary"}
                    </span>
                  </div>

                  <dl className={styles.details}>
                    <div>
                      <dt>Replica count</dt>
                      <dd>
                        {format(
                          snapshot.replication
                            .replica_count,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>WAL level</dt>
                      <dd>
                        {format(
                          snapshot.replication
                            .wal_level,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Archive mode</dt>
                      <dd>
                        {format(
                          snapshot.replication
                            .archive_mode,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Recovery state</dt>
                      <dd>
                        {snapshot.replication
                          .is_standby == null
                          ? "Not available"
                          : snapshot.replication
                                .is_standby
                            ? "In recovery"
                            : "Primary"}
                      </dd>
                    </div>
                  </dl>
                </article>
              </section>

              <section className={styles.panel}>
                <div
                  className={styles.panelHeader}
                >
                  <div>
                    <span className={styles.kicker}>
                      ACTIVITY
                    </span>

                    <h2>
                      Recent Database Activity
                    </h2>
                  </div>

                  <span>
                    Live pg_stat_activity
                  </span>
                </div>

                {snapshot.recent_activity.length ? (
                  <div className={styles.activity}>
                    <div
                      className={
                        styles.activityHead
                      }
                    >
                      <span>Date / Time</span>
                      <span>User / Actor</span>
                      <span>State</span>
                      <span>Details</span>
                    </div>

                    {snapshot.recent_activity.map(
                      (row, index) => (
                        <div
                          key={`${row.pid}-${index}`}
                        >
                          <span>
                            {date(row.query_start)}
                          </span>

                          <strong>
                            {format(row.usename)}
                          </strong>

                          <span>
                            {format(row.state)}
                          </span>

                          <p
                            title={format(
                              row.query,
                            )}
                          >
                            {format(row.query)}
                          </p>
                        </div>
                      ),
                    )}
                  </div>
                ) : (
                  <p className={styles.muted}>
                    No activity rows were available or
                    the database role lacks access to the
                    activity view.
                  </p>
                )}
              </section>

              <footer className={styles.footerFacts}>
                <span>
                  Environment{" "}
                  <strong>
                    {environment.toUpperCase()}
                  </strong>
                </span>

                <span>
                  Status{" "}
                  <strong
                    className={tone(
                      snapshot.status,
                    )}
                  >
                    {snapshot.status}
                  </strong>
                </span>

                <span>
                  Checked{" "}
                  <strong>
                    {date(snapshot.checked_at)}
                  </strong>
                </span>
              </footer>
            </>
          ) : null}
        </section>
      </div>
    </main>
  );
}