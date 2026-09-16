import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  getProjectControlSnapshot,
  ProjectControlApiError,
  ProjectControlSnapshot,
} from "@/app/lib/api/projectControl";

const DEFAULT_PROJECT_ID = "easychatbot";

function statusLabel(
  status: ProjectControlSnapshot["project_status"],
): string {
  switch (status) {
    case "on_track":
      return "ON TRACK";
    case "at_risk":
      return "AT RISK";
    case "blocked":
      return "BLOCKED";
    case "complete":
      return "COMPLETE";
    default:
      return "UNKNOWN";
  }
}

function sourceStatusLabel(
  status: ProjectControlSnapshot["sources"][number]["status"],
): string {
  switch (status) {
    case "available":
      return "Available";
    case "stale":
      return "Stale";
    case "unavailable":
      return "Unavailable";
    default:
      return status;
  }
}

export default function ProjectControlPage() {
  const [snapshot, setSnapshot] =
    useState<ProjectControlSnapshot | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const loadSnapshot = useCallback(
    async () => {
      setLoading(true);
      setError(null);

      try {
        const result =
          await getProjectControlSnapshot(
            DEFAULT_PROJECT_ID,
          );

        setSnapshot(result);
      } catch (cause) {
        if (
          cause instanceof ProjectControlApiError
        ) {
          setError(cause.message);
        } else {
          setError(
            "Unable to load Project Control data.",
          );
        }
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    void loadSnapshot();
  }, [loadSnapshot]);

  if (loading) {
    return (
      <main
        aria-label="Project Control Center"
        style={{
          padding: "32px",
        }}
      >
        <h1>Project Control Center</h1>

        <p role="status">
          Loading project control data…
        </p>
      </main>
    );
  }

  if (error) {
    return (
      <main
        aria-label="Project Control Center"
        style={{
          padding: "32px",
        }}
      >
        <h1>Project Control Center</h1>

        <section
          role="alert"
          aria-label="Project Control error"
        >
          <h2>Project data unavailable</h2>

          <p>{error}</p>

          <button
            type="button"
            onClick={() => {
              void loadSnapshot();
            }}
          >
            Retry
          </button>
        </section>
      </main>
    );
  }

  if (!snapshot) {
    return (
      <main
        aria-label="Project Control Center"
        style={{
          padding: "32px",
        }}
      >
        <h1>Project Control Center</h1>

        <p>
          No project control snapshot is available.
        </p>
      </main>
    );
  }

  const unavailableSources =
    snapshot.sources.filter(
      (source) =>
        source.status !== "available",
    );

  return (
    <main
      aria-label="Project Control Center"
      style={{
        padding: "32px",
        maxWidth: "1400px",
        margin: "0 auto",
      }}
    >
      <header>
        <p>BACK-OFFICE</p>

        <h1>
          {snapshot.project_name}
        </h1>

        <p>
          Project Control Center
        </p>
      </header>

      <section
        aria-label="Project status"
        style={{
          marginTop: "24px",
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "16px",
        }}
      >
        <article>
          <strong>Status</strong>
          <div>
            {statusLabel(
              snapshot.project_status,
            )}
          </div>
        </article>

        <article>
          <strong>Progress</strong>
          <div>
            {snapshot.overall_progress_percent.toFixed(
              1,
            )}
            %
          </div>
        </article>

        <article>
          <strong>Release readiness</strong>
          <div>
            {snapshot.release_readiness}
          </div>
        </article>

        <article>
          <strong>Open blockers</strong>
          <div>
            {snapshot.open_blockers}
          </div>
        </article>

        <article>
          <strong>Open risks</strong>
          <div>
            {snapshot.open_risks}
          </div>
        </article>
      </section>

      <section
        aria-label="Current delivery focus"
        style={{
          marginTop: "32px",
        }}
      >
        <h2>Delivery focus</h2>

        <p>
          <strong>
            Milestone:
          </strong>{" "}
          {snapshot.current_milestone ??
            "Not available"}
        </p>

        <p>
          <strong>
            Workstream:
          </strong>{" "}
          {snapshot.current_workstream ??
            "Not available"}
        </p>
      </section>

      <section
        aria-label="Workstreams"
        style={{
          marginTop: "32px",
        }}
      >
        <h2>Workstreams</h2>

        {snapshot.workstreams.length === 0 ? (
          <p>
            No workstream data available.
          </p>
        ) : (
          <div>
            {snapshot.workstreams.map(
              (workstream) => (
                <article
                  key={
                    workstream.workstream_id
                  }
                  style={{
                    marginBottom: "16px",
                  }}
                >
                  <div>
                    <strong>
                      {workstream.name}
                    </strong>
                  </div>

                  <div>
                    {
                      workstream.completion_percent
                    }
                    %
                  </div>

                  <div>
                    Status:{" "}
                    {workstream.status}
                  </div>
                </article>
              ),
            )}
          </div>
        )}
      </section>

      <section
        aria-label="Open issues"
        style={{
          marginTop: "32px",
        }}
      >
        <h2>Issues</h2>

        {snapshot.issues.length === 0 ? (
          <p>
            No open issues reported.
          </p>
        ) : (
          <ul>
            {snapshot.issues.map(
              (issue) => (
                <li
                  key={issue.issue_id}
                >
                  <strong>
                    {issue.title}
                  </strong>{" "}
                  — {issue.severity}
                </li>
              ),
            )}
          </ul>
        )}
      </section>

      <section
        aria-label="Risks"
        style={{
          marginTop: "32px",
        }}
      >
        <h2>Risks</h2>

        {snapshot.risks.length === 0 ? (
          <p>
            No open risks reported.
          </p>
        ) : (
          <ul>
            {snapshot.risks.map(
              (risk) => (
                <li
                  key={risk.risk_id}
                >
                  <strong>
                    {risk.title}
                  </strong>{" "}
                  — {risk.severity}
                </li>
              ),
            )}
          </ul>
        )}
      </section>

      <section
        aria-label="Data sources"
        style={{
          marginTop: "32px",
        }}
      >
        <h2>Data sources</h2>

        {snapshot.sources.length === 0 ? (
          <p>
            No source information available.
          </p>
        ) : (
          <ul>
            {snapshot.sources.map(
              (source) => (
                <li
                  key={source.source_id}
                >
                  <strong>
                    {source.name}
                  </strong>{" "}
                  —{" "}
                  {sourceStatusLabel(
                    source.status,
                  )}

                  {source.error
                    ? ` — ${source.error}`
                    : ""}
                </li>
              ),
            )}
          </ul>
        )}
      </section>

      {unavailableSources.length > 0 && (
        <aside
          role="status"
          aria-label="Source warning"
          style={{
            marginTop: "32px",
          }}
        >
          <strong>
            Some project-control sources
            are unavailable or stale.
          </strong>
        </aside>
      )}

      <footer
        style={{
          marginTop: "32px",
        }}
      >
        <small>
          Snapshot generated:{" "}
          {snapshot.generated_at}
        </small>
      </footer>
    </main>
  );
}