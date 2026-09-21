"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import styles from "./PersistenceOperations.module.css";
import type { Environment, PersistenceSnapshot } from "./types";

/*
 * EasyChatBot frontend is Vite.
 *
 * Keep API requests relative to the frontend origin.
 * Vite proxies /api to the FastAPI backend at 127.0.0.1:8000.
 *
 * Do NOT use process.env.NEXT_PUBLIC_* here.
 */
const API_BASE = "";

const environments: Array<{ value: Environment; label: string }> = [
  { value: "dev", label: "Development (DEV)" },
  { value: "staging", label: "Staging" },
  { value: "production", label: "Production" },
];

const lifecycle = [
  ["Detect", "Collect current state"],
  ["Plan", "Generate repair plan"],
  ["Review", "Review proposed changes"],
  ["Test", "Test in development"],
  ["Approve", "Approve controlled change"],
  ["Apply", "Apply approved migration"],
  ["Validate", "Validate resulting schema"],
  ["Verify", "Final verification & audit"],
] as const;

function formatDate(value: string | null): string {
  if (!value) return "Not available";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString();
}

function bytes(value: number | null): string {
  if (value == null) return "Not available";

  if (value < 1024 ** 2) {
    return `${Math.round(value / 1024)} KB`;
  }

  if (value < 1024 ** 3) {
    return `${(value / 1024 ** 2).toFixed(1)} MB`;
  }

  return `${(value / 1024 ** 3).toFixed(2)} GB`;
}

function statusText(value: string): string {
  return value.replaceAll("_", " ");
}

function stateTone(value: string): string {
  if (["IN_SYNC", "COMPATIBLE", "INFO"].includes(value)) {
    return styles.good;
  }

  if (["PENDING", "MEDIUM", "NOT_CONFIGURED"].includes(value)) {
    return styles.warn;
  }

  return styles.bad;
}

function Icon({
  name,
}: {
  name:
    | "home"
    | "health"
    | "database"
    | "project"
    | "agents"
    | "shield"
    | "monitor"
    | "logs"
    | "settings"
    | "branch"
    | "schema"
    | "cube"
    | "refresh"
    | "check"
    | "plan"
    | "lock";
}) {
  const paths: Record<string, string> = {
    home: "M3 10.5 12 3l9 7.5M5.5 9.5V21h13V9.5M9 21v-6h6v6",
    health: "M4 13h4l2-8 4 14 2-6h4",
    database:
      "M5 5c0-1.1 3.1-2 7-2s7 .9 7 2-3.1 2-7 2-7-.9-7-2Zm0 0v7c0 1.1 3.1 2 7 2s7-.9 7-2V5M5 12v7c0 1.1 3.1 2 7 2s7-.9 7-2v-7",
    project:
      "M4 7h16v13H4zM8 4h8v3H8zM8 12h8M8 16h5",
    agents:
      "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 9a7 7 0 0 1 14 0M17 8h4M19 6v4",
    shield:
      "m12 3 8 3v5c0 5-3.3 8.7-8 10-4.7-1.3-8-5-8-10V6l8-3Zm-3 9 2 2 4-5",
    monitor: "M4 5h16v11H4zM8 21h8M12 16v5",
    logs: "M6 4h12v16H6zM9 8h6M9 12h6M9 16h4",
    settings:
      "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm0-5v3m0 8v8M3 12h3m12 0h3M5.6 5.6l2.1 2.1m6.6 6.6 2.1 2.1m0-10.8-2.1 2.1m-6.6 6.6-2.1 2.1",
    branch:
      "M6 4v10a4 4 0 0 0 4 4h8M6 8h7a3 3 0 0 0 3-3V4M18 16l3 2-3 2",
    schema:
      "M5 5h14v14H5zM9 5v14M5 10h14M9 15h10",
    cube:
      "m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Zm0 0v9m8-4.5-8 4.5m0 0-8-4.5",
    refresh:
      "M20 11a8 8 0 0 0-14-4L4 9m0-4v4h4M4 13a8 8 0 0 0 14 4l2-2m0 4v-4h-4",
    check: "m5 12 4 4L19 6",
    plan:
      "M6 3h9l3 3v15H6zM15 3v4h3M9 12h6M9 16h5",
    lock:
      "M7 10V7a5 5 0 0 1 10 0v3m-12 0h14v10H5z",
  };

  return (
    <svg
      className={styles.svgIcon}
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  );
}

function EnvironmentSelect({
  value,
  onChange,
}: {
  value: Environment;
  onChange: (value: Environment) => void;
}) {
  return (
    <label className={styles.environmentSelect}>
      <span>Environment</span>

      <select
        value={value}
        onChange={(event) =>
          onChange(event.target.value as Environment)
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
  );
}

function Sidebar({
  environment,
  setEnvironment,
}: {
  environment: Environment;
  setEnvironment: (value: Environment) => void;
}) {
  const items = [
    ["home", "Overview", "/operations-center"],
    [
      "health",
      "Functionality Health",
      "/operations-center/functionality-health",
    ],
    [
      "database",
      "Persistence Control",
      "/operations-center/persistence",
    ],
    ["project", "Project Control", "/project-control"],
    ["agents", "Agents", "/operations-center/agents"],
    [
      "health",
      "Quality Management",
      "/operations-center/functionality-health",
    ],
    [
      "shield",
      "Security & Governance",
      "/operations-center/governance",
    ],
    [
      "monitor",
      "Monitoring",
      "/operations-center/compliance/cmp/risk-intelligence/risk-coverage",
    ],
    [
      "logs",
      "Logs",
      "/operations-center/governance",
    ],
    [
      "settings",
      "Configuration",
      "/operations-center/configuration",
    ],
  ] as const;

  return (
    <aside className={styles.sidebar}>
      <div className={styles.sideSectionLabel}>
        OPERATIONS CENTER
      </div>

      <nav
        className={styles.sideNav}
        aria-label="Operations Center"
      >
        {items.map(([icon, label, href]) =>
          href ? (
            <a
              key={label}
              href={href}
              className={`${styles.navItem} ${
                label === "Persistence Control"
                  ? styles.active
                  : ""
              }`}
            >
              <Icon
                name={
                  icon as
                    | "home"
                    | "health"
                    | "database"
                    | "project"
                    | "agents"
                    | "shield"
                    | "monitor"
                    | "logs"
                    | "settings"
                }
              />
              <span>{label}</span>
            </a>
          ) : (
            <span
              key={label}
              className={`${styles.navItem} ${styles.navDisabled}`}
              aria-disabled="true"
            >
              <Icon
                name={
                  icon as
                    | "home"
                    | "health"
                    | "database"
                    | "project"
                    | "agents"
                    | "shield"
                    | "monitor"
                    | "logs"
                    | "settings"
                }
              />
              <span>{label}</span>
            </span>
          ),
        )}
      </nav>

      <div className={styles.sideBottom}>
        <EnvironmentSelect
          value={environment}
          onChange={setEnvironment}
        />

        <div className={styles.helpCard}>
          <div className={styles.helpIcon}>?</div>

          <div>
            <strong>Need help?</strong>
            <span>
              Review guidance before changing persistence
              state.
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default function PersistenceOperationsPage() {
  const [environment, setEnvironment] =
    useState<Environment>("dev");

  const [snapshot, setSnapshot] =
    useState<PersistenceSnapshot | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [notice, setNotice] =
    useState<string | null>(null);

  const [showPlan, setShowPlan] = useState(false);

  const refresh = useCallback(
    async (
      purpose: "refresh" | "validate" = "refresh",
    ) => {
      setLoading(true);
      setError(null);
      setNotice(null);

      try {
        const response = await fetch(
          `${API_BASE}/api/operations-center/persistence?environment=${environment}`,
          {
            cache: "no-store",
          },
        );

        if (!response.ok) {
          throw new Error(
            `Persistence API returned HTTP ${response.status}.`,
          );
        }

        const data =
          (await response.json()) as PersistenceSnapshot;

        setSnapshot(data);

        if (purpose === "validate") {
          setNotice(
            `Validation completed for ${data.environment.toUpperCase()} using live PostgreSQL and migration diagnostics.`,
          );
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load persistence diagnostics.",
        );
      } finally {
        setLoading(false);
      }
    },
    [environment],
  );

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const recommendationTone = useMemo(
    () =>
      stateTone(
        snapshot?.recommendation.severity ??
          "UNKNOWN",
      ),
    [snapshot],
  );

  const selectedEnvironment =
    environments.find(
      (item) => item.value === environment,
    )?.label ?? environment;

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

          <EnvironmentSelect
            value={environment}
            onChange={setEnvironment}
          />
        </div>
      </header>

      <div className={styles.layout}>
        <Sidebar
          environment={environment}
          setEnvironment={setEnvironment}
        />

        <section className={styles.content}>
          <div className={styles.breadcrumb}>
            <a href="/operations-center">
              Operations Center
            </a>

            <span>›</span>

            <span>Persistence Operations</span>
          </div>

          <header className={styles.pageHeader}>
            <div>
              <div className={styles.kicker}>
                PERSISTENCE CONTROL ·{" "}
                {selectedEnvironment.toUpperCase()}
              </div>

              <h1>Persistence Operations Center</h1>

              <p>
                Monitor, diagnose and safely evolve
                EasyWorld persistence.
              </p>
            </div>

            <div className={styles.headerMeta}>
              <span>
                Last updated
                <br />
                <strong>
                  {snapshot
                    ? formatDate(snapshot.checked_at)
                    : "—"}
                </strong>
              </span>

              <button
                className={styles.secondaryButton}
                onClick={() => void refresh()}
                disabled={loading}
              >
                <Icon name="refresh" /> Refresh
              </button>
            </div>
          </header>

          <nav
            className={styles.tabs}
            aria-label="Persistence sections"
          >
            <span className={styles.tabActive}>
              Overview
            </span>

            <a href="/operations-center/persistence/health">
              Database Health &amp; Operations
            </a>

            <a href="#migrations">Migrations</a>
            <a href="#schema">Schema</a>
            <a href="#guidance">Guidance</a>
          </nav>

          {loading && !snapshot ? (
            <div className={styles.notice}>
              <span className={styles.spinner} />
              Loading live persistence diagnostics…
            </div>
          ) : null}

          {error ? (
            <div
              className={`${styles.notice} ${styles.errorNotice}`}
              role="alert"
            >
              <strong>Diagnostics unavailable.</strong>

              <span>{error}</span>

              <button
                onClick={() => void refresh()}
              >
                Retry
              </button>
            </div>
          ) : null}

          {notice ? (
            <div className={styles.notice}>
              <Icon name="check" />

              <span>{notice}</span>

              <button
                onClick={() => setNotice(null)}
                aria-label="Dismiss message"
              >
                ×
              </button>
            </div>
          ) : null}

          {snapshot ? (
            <>
              <section
                className={styles.statusGrid}
                aria-label="Persistence status summary"
              >
                <article className={styles.statusCard}>
                  <div className={styles.cardTitle}>
                    <span className={styles.iconTile}>
                      <Icon name="database" />
                    </span>

                    <div>
                      <strong>Database</strong>

                      <span
                        className={
                          snapshot.database.connected
                            ? styles.good
                            : styles.bad
                        }
                      >
                        {snapshot.database.connected
                          ? "Connected"
                          : "Unavailable"}
                      </span>
                    </div>
                  </div>

                  <strong className={styles.bigMetric}>
                    {snapshot.database.postgres_version ??
                      "—"}
                  </strong>

                  <span className={styles.subMetric}>
                    {snapshot.database.database ??
                      "Database unavailable"}
                  </span>

                  <span className={styles.cardFoot}>
                    Latency{" "}
                    {snapshot.database.latency_ms ==
                    null
                      ? "—"
                      : `${snapshot.database.latency_ms} ms`}
                  </span>
                </article>

                <article
                  id="migrations"
                  className={styles.statusCard}
                >
                  <div className={styles.cardTitle}>
                    <span className={styles.iconTile}>
                      <Icon name="branch" />
                    </span>

                    <div>
                      <strong>Migrations</strong>

                      <span
                        className={stateTone(
                          snapshot.migration.graph,
                        )}
                      >
                        {statusText(
                          snapshot.migration.graph,
                        )}
                      </span>
                    </div>
                  </div>

                  <strong className={styles.bigMetric}>
                    {
                      snapshot.migration
                        .database_revisions.length
                    }{" "}
                    revisions
                  </strong>

                  <span className={styles.subMetric}>
                    {
                      snapshot.migration.repository_heads
                        .length
                    }{" "}
                    repository head(s)
                  </span>

                  <span className={styles.cardFoot}>
                    {
                      snapshot.migration.missing_revisions
                        .length
                    }{" "}
                    missing ·{" "}
                    {snapshot.migration
                      .pending_migrations?.length ??
                      0}{" "}
                    pending
                  </span>
                </article>

                <article
                  id="schema"
                  className={styles.statusCard}
                >
                  <div className={styles.cardTitle}>
                    <span className={styles.iconTile}>
                      <Icon name="schema" />
                    </span>

                    <div>
                      <strong>Schema</strong>

                      <span
                        className={stateTone(
                          snapshot.schema.state,
                        )}
                      >
                        {statusText(
                          snapshot.schema.state,
                        )}
                      </span>
                    </div>
                  </div>

                  <strong className={styles.bigMetric}>
                    {snapshot.schema.tables_inspected}{" "}
                    tables
                  </strong>

                  <span className={styles.subMetric}>
                    {snapshot.schema.tables_with_drift}{" "}
                    table(s) with drift
                  </span>

                  <span className={styles.cardFoot}>
                    {snapshot.schema.differences.length}{" "}
                    detected difference(s)
                  </span>
                </article>

                <article className={styles.statusCard}>
                  <div className={styles.cardTitle}>
                    <span className={styles.iconTile}>
                      <Icon name="cube" />
                    </span>

                    <div>
                      <strong>Application</strong>

                      <span
                        className={stateTone(
                          snapshot.compatibility
                            .state,
                        )}
                      >
                        {statusText(
                          snapshot.compatibility
                            .state,
                        )}
                      </span>
                    </div>
                  </div>

                  <strong className={styles.bigMetric}>
                    {snapshot.compatibility
                      .application_version ??
                      "Not configured"}
                  </strong>

                  <span className={styles.subMetric}>
                    Expected schema{" "}
                    {snapshot.compatibility
                      .expected_schema_revision ??
                      "not configured"}
                  </span>

                  <span className={styles.cardFoot}>
                    Actual:{" "}
                    {snapshot.compatibility
                      .actual_database_revisions.join(
                        ", ",
                      ) || "—"}
                  </span>
                </article>
              </section>

              <section
                className={`${styles.recommendation} ${recommendationTone}`}
              >
                <div className={styles.recTop}>
                  <span className={styles.alertIcon}>
                    {snapshot.recommendation
                      .severity === "INFO"
                      ? "✓"
                      : "!"}
                  </span>

                  <div className={styles.recTitle}>
                    <span className={styles.kicker}>
                      WHAT SHOULD I DO NOW?
                    </span>

                    <h2>
                      {snapshot.recommendation.title}
                    </h2>

                    <p>
                      {snapshot.recommendation.summary}
                    </p>
                  </div>

                  <span className={styles.timing}>
                    {statusText(
                      snapshot.recommendation.timing,
                    )}
                  </span>
                </div>

                <div className={styles.recColumns}>
                  <div>
                    <strong>Why?</strong>
                    <p>
                      {snapshot.recommendation.why}
                    </p>

                    <strong>Impact</strong>
                    <p>
                      {snapshot.recommendation.impact}
                    </p>
                  </div>

                  <div>
                    <strong>Recommended action</strong>

                    <ol>
                      {snapshot.recommendation.next_actions.map(
                        (item, index) => (
                          <li key={item}>
                            <b>{index + 1}</b>
                            <span>{item}</span>
                          </li>
                        ),
                      )}
                    </ol>
                  </div>

                  {snapshot.recommendation
                    .blocked_actions.length > 0 ? (
                    <div className={styles.blocked}>
                      <strong>Do not</strong>

                      <ul>
                        {snapshot.recommendation.blocked_actions.map(
                          (item) => (
                            <li key={item}>
                              × <span>{item}</span>
                            </li>
                          ),
                        )}
                      </ul>
                    </div>
                  ) : null}
                </div>
              </section>

              <div className={styles.actionBar}>
                <button
                  className={styles.primaryButton}
                  onClick={() => void refresh()}
                  disabled={loading}
                >
                  <Icon name="refresh" />
                  Refresh Diagnostics
                </button>

                <button
                  className={styles.secondaryButton}
                  onClick={() =>
                    void refresh("validate")
                  }
                  disabled={loading}
                >
                  <Icon name="check" />
                  Validate Database
                </button>

                <button
                  className={styles.secondaryButton}
                  onClick={() =>
                    setShowPlan((value) => !value)
                  }
                >
                  <Icon name="plan" />

                  {showPlan
                    ? "Hide Repair Plan"
                    : "Generate Repair Plan"}
                </button>

                <button
                  className={styles.lockedButton}
                  disabled
                  title="Migration execution is intentionally disabled in this diagnostic release."
                >
                  <Icon name="lock" />
                  Apply Approved Migrations
                </button>

                <a
                  className={styles.secondaryButton}
                  href="#guidance"
                >
                  What Should I Do?
                </a>
              </div>

              {showPlan ? (
                <section
                  className={styles.planPanel}
                  aria-live="polite"
                >
                  <div className={styles.panelHeader}>
                    <div>
                      <span className={styles.kicker}>
                        READ-ONLY CONTROL PLAN
                      </span>

                      <h2>
                        Recommended repair sequence
                      </h2>
                    </div>

                    <span className={styles.planBadge}>
                      No changes applied
                    </span>
                  </div>

                  <p>
                    Generated from the current live
                    recommendation. This release
                    deliberately does not execute
                    migrations or alter{" "}
                    <code>alembic_version</code>.
                  </p>

                  <ol className={styles.planList}>
                    {snapshot.recommendation.next_actions.map(
                      (item, index) => (
                        <li key={item}>
                          <span>{index + 1}</span>

                          <div>
                            <strong>{item}</strong>

                            <small>
                              {index === 0
                                ? "Start from observed state."
                                : index ===
                                    snapshot
                                      .recommendation
                                      .next_actions
                                      .length -
                                      1
                                  ? "Confirm the resulting state."
                                  : "Requires review and appropriate approval."}
                            </small>
                          </div>
                        </li>
                      ),
                    )}
                  </ol>
                </section>
              ) : null}

              <section className={styles.threeGrid}>
                <article className={styles.panel}>
                  <div className={styles.panelHeader}>
                    <div>
                      <span className={styles.kicker}>
                        CONTROL WORKFLOW
                      </span>

                      <h2>Migration Lifecycle</h2>
                    </div>

                    <a href="/operations-center/persistence/health">
                      Database diagnostics →
                    </a>
                  </div>

                  <ol className={styles.lifecycle}>
                    {lifecycle.map(
                      ([step, description], index) => (
                        <li
                          key={step}
                          className={
                            index === 0
                              ? styles.lifecycleCurrent
                              : ""
                          }
                        >
                          <span>
                            {index === 0 ? "✓" : index + 1}
                          </span>

                          <div>
                            <strong>{step}</strong>
                            <small>{description}</small>
                          </div>
                        </li>
                      ),
                    )}
                  </ol>
                </article>

                <article className={styles.panel}>
                  <div className={styles.panelHeader}>
                    <div>
                      <span className={styles.kicker}>
                        ALEMBIC STATE
                      </span>

                      <h2>Migration Lineage</h2>
                    </div>

                    <span>Repository state</span>
                  </div>

                  {snapshot.migration.migration_history
                    .length ? (
                    <div
                      className={styles.lineageList}
                    >
                      {snapshot.migration.migration_history
                        .slice(0, 8)
                        .map((item) => (
                          <div key={item.revision}>
                            <code>
                              {item.revision}
                            </code>

                            <span
                              className={
                                item.status === "CURRENT"
                                  ? styles.good
                                  : item.status ===
                                        "PENDING" ||
                                      item.status ===
                                        "UNKNOWN_DATABASE_REVISION"
                                    ? styles.bad
                                    : styles.muted
                              }
                            >
                              {statusText(
                                item.status,
                              )}
                            </span>
                          </div>
                        ))}
                    </div>
                  ) : (
                    <p className={styles.muted}>
                      Migration lineage is unavailable
                      until the repository graph can be
                      loaded.
                    </p>
                  )}
                </article>

                <article className={styles.panel}>
                  <div className={styles.panelHeader}>
                    <div>
                      <span className={styles.kicker}>
                        AUDIT EVIDENCE
                      </span>

                      <h2>Recent Control Action</h2>
                    </div>

                    <span>Live</span>
                  </div>

                  {snapshot.last_action ? (
                    <dl className={styles.details}>
                      <div>
                        <dt>Action</dt>
                        <dd>
                          {snapshot.last_action.action}
                        </dd>
                      </div>

                      <div>
                        <dt>Functionality</dt>
                        <dd>
                          {
                            snapshot.last_action
                              .functionality_id
                          }
                        </dd>
                      </div>

                      <div>
                        <dt>Environment</dt>
                        <dd>
                          {
                            snapshot.last_action
                              .environment
                          }
                        </dd>
                      </div>

                      <div>
                        <dt>Actor</dt>
                        <dd>
                          {snapshot.last_action.actor}
                        </dd>
                      </div>

                      <div>
                        <dt>Changed</dt>
                        <dd>
                          {formatDate(
                            snapshot.last_action
                              .changed_at,
                          )}
                        </dd>
                      </div>
                    </dl>
                  ) : (
                    <p className={styles.muted}>
                      No functionality-control audit
                      action is available. Migration
                      execution history is not inferred
                      from Alembic’s version table.
                    </p>
                  )}
                </article>
              </section>

              <section className={styles.lowerGrid}>
                <article
                  id="guidance"
                  className={styles.panel}
                >
                  <div className={styles.panelHeader}>
                    <div>
                      <span className={styles.kicker}>
                        ENGINEERING GUIDANCE
                      </span>

                      <h2>
                        When Do I Need a Migration?
                      </h2>
                    </div>

                    <span>Rules of thumb</span>
                  </div>

                  <p className={styles.guidanceLead}>
                    Create a migration when a change
                    modifies persistent database structure
                    or database objects.
                  </p>

                  <div className={styles.guidanceGrid}>
                    <span>
                      ✓ Add / remove column
                    </span>
                    <span>
                      ✓ Add / remove table
                    </span>
                    <span>✓ Change index</span>
                    <span>✓ Change constraint</span>
                    <span>
                      ✓ Change enum / type
                    </span>
                    <span>× UI / CSS changes</span>
                    <span>
                      × Frontend components
                    </span>
                    <span>
                      × Python calculations
                    </span>
                  </div>
                </article>

                <article className={styles.panel}>
                  <div className={styles.panelHeader}>
                    <div>
                      <span className={styles.kicker}>
                        ENVIRONMENT CONTRACT
                      </span>

                      <h2>
                        Environment Compatibility
                      </h2>
                    </div>

                    <span>Live</span>
                  </div>

                  <div
                    className={styles.environmentRows}
                  >
                    <div>
                      <span>Selected</span>
                      <strong>
                        {snapshot.environment.toUpperCase()}
                      </strong>
                    </div>

                    <div>
                      <span>Application</span>
                      <strong>
                        {snapshot.compatibility
                          .application_version ??
                          "Not configured"}
                      </strong>
                    </div>

                    <div>
                      <span>Expected schema</span>
                      <strong>
                        {snapshot.compatibility
                          .expected_schema_revision ??
                          "Not configured"}
                      </strong>
                    </div>

                    <div>
                      <span>Compatibility</span>
                      <strong
                        className={stateTone(
                          snapshot.compatibility
                            .state,
                        )}
                      >
                        {statusText(
                          snapshot.compatibility.state,
                        )}
                      </strong>
                    </div>
                  </div>

                  <p className={styles.muted}>
                    Source:{" "}
                    {snapshot.compatibility.source}
                  </p>
                </article>
              </section>

              <footer className={styles.footerFacts}>
                <span>
                  Database size{" "}
                  <strong>
                    {bytes(
                      snapshot.database
                        .database_size_bytes,
                    )}
                  </strong>
                </span>

                <span>
                  Connections{" "}
                  <strong>
                    {snapshot.database
                      .active_connections ?? "—"}{" "}
                    /{" "}
                    {snapshot.database
                      .max_connections ?? "—"}
                  </strong>
                </span>

                <span>
                  SSL{" "}
                  <strong>
                    {snapshot.database.ssl_enabled ==
                    null
                      ? "Not available"
                      : snapshot.database.ssl_enabled
                        ? "Enabled"
                        : "Disabled"}
                  </strong>
                </span>

                <span>
                  Recommendation{" "}
                  <strong
                    className={recommendationTone}
                  >
                    {statusText(
                      snapshot.recommendation
                        .severity,
                    )}
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