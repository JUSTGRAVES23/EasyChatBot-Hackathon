import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  getProjectControlSnapshot,
  ProjectControlApiError,
  type ProjectControlSnapshot,
} from "@/app/lib/api/projectControl";
import {
  getProjectRegistryProject,
  ProjectRegistryApiError,
  type ProjectRegistryProject,
} from "@/app/lib/api/projectRegistry";

import styles from "../../ProjectControlPage.module.css";

function statusLabel(status: ProjectControlSnapshot["project_status"]): string {
  switch (status) {
    case "on_track": return "ON TRACK";
    case "at_risk": return "AT RISK";
    case "blocked": return "BLOCKED";
    case "complete": return "COMPLETE";
    default: return "UNKNOWN";
  }
}

function statusTone(status: string): string {
  if (["on_track", "available", "complete", "resolved", "done"].includes(status)) return "success";
  if (["at_risk", "stale", "in_progress"].includes(status)) return "warning";
  if (["blocked", "unavailable", "open", "cancelled"].includes(status)) return "danger";
  return "neutral";
}

function severityTone(severity: string): string {
  const value = severity.toLowerCase();
  if (value === "critical" || value === "high") return "danger";
  if (value === "medium") return "warning";
  return "neutral";
}

function formatDate(value: string | null): string {
  if (!value) return "Not available";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function formatWholePercent(value: number): string {
  return `${Math.max(0, Math.min(100, value)).toFixed(0)}%`;
}

function formatReadiness(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return "Not available";
  const numeric = Number(trimmed.replace(/%$/, ""));
  return Number.isFinite(numeric)
    ? `${Math.max(0, Math.min(100, numeric)).toFixed(1)}%`
    : trimmed;
}

export default function ProjectControlProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectRegistryProject | null>(null);
  const [snapshot, setSnapshot] = useState<ProjectControlSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProject = useCallback(async () => {
    const id = projectId?.trim();
    if (!id) {
      setError("Project ID is required.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [registryProject, projectSnapshot] = await Promise.all([
        getProjectRegistryProject(id),
        getProjectControlSnapshot(id),
      ]);
      setProject(registryProject);
      setSnapshot(projectSnapshot);
    } catch (cause) {
      if (cause instanceof ProjectRegistryApiError || cause instanceof ProjectControlApiError) {
        setError(cause.message);
      } else {
        setError("Unable to load the selected project.");
      }
      setProject(null);
      setSnapshot(null);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void loadProject();
  }, [loadProject]);

  const unavailableSources = useMemo(
    () => snapshot?.sources.filter((source) => source.status !== "available") ?? [],
    [snapshot],
  );

  if (loading) {
    return (
      <main className={styles.page} aria-label="Project Control Project Detail">
        <section className={styles.loadingPanel} role="status">
          <p className={styles.eyebrow}>PROJECT CONTROL CENTER</p>
          <h1>Loading project</h1>
          <p>Loading authoritative project information...</p>
        </section>
      </main>
    );
  }

  if (error || !project || !snapshot) {
    return (
      <main className={styles.page} aria-label="Project Control Project Detail">
        <section className={styles.errorPanel} role="alert">
          <p className={styles.eyebrow}>PROJECT CONTROL CENTER</p>
          <h1>Project unavailable</h1>
          <p>{error ?? "No authoritative project-control snapshot is available."}</p>
          <button type="button" className={styles.primaryButton} onClick={() => void loadProject()}>
            Retry
          </button>
          <button type="button" className={styles.secondaryButton} onClick={() => navigate("/project-control")}>
            Back to Project Control
          </button>
        </section>
      </main>
    );
  }

  const progress = Math.max(0, Math.min(100, snapshot.overall_progress_percent));

  return (
    <main className={styles.page} aria-label={`${project.name} Project Control`}>
      <div className={styles.atmosphere} aria-hidden="true" />
      <div className={styles.content}>
        <nav className={styles.breadcrumb} aria-label="Breadcrumb">
          <Link to="/project-control">Project Control Center</Link>
          <span aria-hidden="true">&gt;</span>
          <strong>{project.name}</strong>
        </nav>

        <section className={styles.hero}>
          <div className={styles.heroContent}>
            <p className={styles.eyebrow}>PROJECT CONTROL CENTER</p>
            <h1>{project.name}</h1>
            <p className={styles.heroSubtitle}>
              {project.description || "Registered project tracked through Project Control."}
            </p>
            <div className={styles.cardMeta}>
              <span>Project ID: {project.project_id}</span>
              <span>Owner: {project.owner ?? "Not assigned"}</span>
              <span>Registry status: {project.active ? "Active" : "Inactive"}</span>
              <span>Created: {formatDate(project.created_at)}</span>
            </div>
          </div>
          <div>
            <button type="button" className={styles.primaryButton} onClick={() => navigate("/project-control")}>Back to Portfolio</button>
          </div>
        </section>

        <section className={styles.kpiGrid} aria-label="Project status">
          <article className={styles.kpiCard}>
            <span className={styles.kpiIcon} data-tone={statusTone(snapshot.project_status)}>*</span>
            <div><span className={styles.kpiLabel}>Project Status</span><strong>{statusLabel(snapshot.project_status)}</strong><small>Current delivery state</small></div>
          </article>
          <article className={styles.kpiCard}>
            <span className={styles.progressRing} style={{ "--progress": `${progress}%` } as React.CSSProperties}><span>{formatWholePercent(progress)}</span></span>
            <div><span className={styles.kpiLabel}>Overall Progress</span><strong>{formatWholePercent(progress)}</strong><small>Across current scope</small></div>
          </article>
          <article className={styles.kpiCard}>
            <span className={styles.kpiIcon} data-tone="success">*</span>
            <div><span className={styles.kpiLabel}>Release Readiness</span><strong>{formatReadiness(snapshot.release_readiness)}</strong><small>Current readiness assessment</small></div>
          </article>
          <article className={styles.kpiCard}>
            <span className={styles.kpiIcon} data-tone="danger">!</span>
            <div><span className={styles.kpiLabel}>Open Blockers</span><strong>{snapshot.open_blockers}</strong><small>Require attention</small></div>
          </article>
          <article className={styles.kpiCard}>
            <span className={styles.kpiIcon} data-tone="warning">!</span>
            <div><span className={styles.kpiLabel}>Open Risks</span><strong>{snapshot.open_risks}</strong><small>Active risk exposure</small></div>
          </article>
        </section>

        <section className={styles.focusProgressGrid}>
          <article className={styles.panel}>
            <div className={styles.panelHeader}><div><span className={styles.panelKicker}>DELIVERY FOCUS</span><h2>Current Focus</h2></div></div>
            <div className={styles.focusCards}>
              <div className={styles.focusCard}><span className={styles.focusIcon}>M</span><div><span>Current Milestone</span><strong>{snapshot.current_milestone ?? "Not available"}</strong></div></div>
              <div className={styles.focusCard}><span className={styles.focusIcon}>W</span><div><span>Current Workstream</span><strong>{snapshot.current_workstream ?? "Not available"}</strong></div></div>
            </div>
          </article>
          <article className={styles.panel}>
            <div className={styles.panelHeader}><div><span className={styles.panelKicker}>DELIVERY SIGNAL</span><h2>Project Progress</h2></div><strong className={styles.progressValue}>{formatWholePercent(progress)}</strong></div>
            <div className={styles.largeProgress}><div className={styles.largeProgressTrack}><span style={{ width: `${progress}%` }} /></div><div className={styles.progressScale}><span>0%</span><span>Current delivery</span><span>100%</span></div></div>
            <p className={styles.panelNote}>Progress is derived from the authoritative Project Control snapshot.</p>
          </article>
        </section>

        <section className={styles.panel} aria-label="Workstreams">
          <div className={styles.panelHeader}><div><span className={styles.panelKicker}>DELIVERY PORTFOLIO</span><h2>Workstreams <small>({snapshot.workstreams.length})</small></h2></div></div>
          {snapshot.workstreams.length === 0 ? <p className={styles.emptyText}>No workstream data available.</p> : <div className={styles.workstreamGrid}>{snapshot.workstreams.map((item) => <article className={styles.workstreamCard} key={item.workstream_id}><div className={styles.cardTopline}><strong>{item.name}</strong><span className={styles.miniBadge} data-tone={statusTone(item.status)}>* {item.status.replaceAll("_", " ")}</span></div><div className={styles.workstreamPercent}>{formatWholePercent(item.completion_percent)}</div><div className={styles.progressTrack}><span style={{ width: `${Math.max(0, Math.min(100, item.completion_percent))}%` }} /></div><div className={styles.cardMeta}><span>{item.source}</span><span>{formatDate(item.updated_at)}</span></div></article>)}</div>}
        </section>

        {snapshot.metrics.length > 0 && <section className={styles.panel} aria-label="Operational metrics"><div className={styles.panelHeader}><div><span className={styles.panelKicker}>OBSERVED SIGNALS</span><h2>Operational Metrics <small>({snapshot.metrics.length})</small></h2></div></div><div className={styles.metricGrid}>{snapshot.metrics.map((metric) => <article className={styles.metricCard} key={metric.key}><span>{metric.label}</span><strong>{String(metric.value ?? "-")}{metric.unit ? <span className={styles.metricUnit}> {metric.unit}</span> : null}</strong><small>{metric.source} | {formatDate(metric.observed_at)}</small></article>)}</div></section>}

        <section className={styles.twoColumnGrid}>
          <article className={styles.panel} aria-label="Open issues"><div className={styles.panelHeader}><div><span className={styles.panelKicker}>CONTROL EXCEPTIONS</span><h2>Open Issues <small>({snapshot.issues.length})</small></h2></div></div>{snapshot.issues.length === 0 ? <p className={styles.emptyText}>No open issues reported.</p> : <div className={styles.table}><div className={styles.tableHeader}><span>Issue</span><span>Severity</span><span>Status</span></div>{snapshot.issues.map((issue) => <div className={styles.tableRow} key={issue.issue_id}><div><strong>{issue.title}</strong><small>{issue.owner ?? "Owner not assigned"}</small></div><span className={styles.miniBadge} data-tone={severityTone(issue.severity)}>{issue.severity}</span><span className={styles.miniBadge} data-tone={statusTone(issue.status)}>{issue.status.replaceAll("_", " ")}</span></div>)}</div>}</article>
          <article className={styles.panel} aria-label="Active risks"><div className={styles.panelHeader}><div><span className={styles.panelKicker}>RISK REGISTER</span><h2>Active Risks <small>({snapshot.risks.length})</small></h2></div></div>{snapshot.risks.length === 0 ? <p className={styles.emptyText}>No open risks reported.</p> : <div className={styles.table}><div className={styles.tableHeader}><span>Risk</span><span>Severity</span><span>Status</span></div>{snapshot.risks.map((risk) => <div className={styles.tableRow} key={risk.risk_id}><div><strong>{risk.title}</strong><small>{risk.owner ?? "Owner not assigned"}</small></div><span className={styles.miniBadge} data-tone={severityTone(risk.severity)}>{risk.severity}</span><span className={styles.miniBadge} data-tone={statusTone(risk.status)}>{risk.status.replaceAll("_", " ")}</span></div>)}</div>}</article>
        </section>

        <section className={styles.twoColumnGrid}>
          <article className={styles.panel} aria-label="Open actions"><div className={styles.panelHeader}><div><span className={styles.panelKicker}>EXECUTION REGISTER</span><h2>Open Actions <small>({snapshot.actions.length})</small></h2></div></div>{snapshot.actions.length === 0 ? <p className={styles.emptyText}>No actions reported.</p> : <div className={styles.table}><div className={styles.tableHeader}><span>Action</span><span>Priority</span><span>Due</span></div>{snapshot.actions.map((action) => <div className={styles.tableRow} key={action.action_id}><div><strong>{action.title}</strong><small>{action.status.replaceAll("_", " ")}</small></div><span className={styles.miniBadge} data-tone={severityTone(action.priority)}>{action.priority}</span><span className={styles.tableDate}>{formatDate(action.due_at)}</span></div>)}</div>}</article>
          <article className={styles.panel} aria-label="Upcoming milestones"><div className={styles.panelHeader}><div><span className={styles.panelKicker}>ROADMAP</span><h2>Upcoming Milestones <small>({snapshot.milestones.length})</small></h2></div></div>{snapshot.milestones.length === 0 ? <p className={styles.emptyText}>No milestone data available.</p> : <div className={styles.milestoneList}>{snapshot.milestones.map((milestone) => <div className={styles.milestoneRow} key={milestone.milestone_id}><div><strong>{milestone.name}</strong><small>{milestone.source}</small></div><span className={styles.miniBadge} data-tone={statusTone(milestone.status)}>{milestone.status.replaceAll("_", " ")}</span><time>{formatDate(milestone.target_date)}</time></div>)}</div>}</article>
        </section>

        <section className={styles.panel} aria-label="Data sources"><div className={styles.panelHeader}><div><span className={styles.panelKicker}>EVIDENCE LAYER</span><h2>Authoritative Data Sources <small>({snapshot.sources.length})</small></h2></div>{unavailableSources.length > 0 && <span className={styles.sourceWarning}>{unavailableSources.length} source{unavailableSources.length === 1 ? "" : "s"} need attention</span>}</div>{snapshot.sources.length === 0 ? <p className={styles.emptyText}>No source information available.</p> : <ul className={styles.sourceList}>{snapshot.sources.map((source) => <li className={styles.sourceListItem} key={source.source_id}><article className={styles.sourceCard}><div className={styles.sourceIcon}>*</div><div className={styles.sourceBody}><strong>{source.name}</strong><span className={styles.miniBadge} data-tone={statusTone(source.status)}>* {source.status}</span><small>{source.status === "available" ? `Updated ${formatDate(source.updated_at)}` : source.error ?? "Source unavailable"}</small></div></article></li>)}</ul>}</section>
      </div>
    </main>
  );
}
