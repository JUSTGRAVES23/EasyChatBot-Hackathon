import { useCallback, useEffect, useRef, useState } from "react";
import type { CSSProperties, FormEvent } from "react";
import {
  createProjectRegistryProject,
  exportProjectRegistry,
  importProjectRegistry,
  listProjectRegistryProjects,
  ProjectRegistryApiError,
  type CreateProjectRegistryProject,
  type ProjectRegistryImportMode,
  type ProjectRegistryProject,
  updateProjectRegistryProject,
  type UpdateProjectRegistryProject,
} from "@/app/lib/api/projectRegistry";

const MAX_FILE_BYTES = 5 * 1024 * 1024;

const styles: Record<string, CSSProperties> = {
  page: { minHeight: "100vh", padding: "2rem", background: "var(--background, #0b1020)", color: "var(--foreground, #f5f7fb)" },
  content: { maxWidth: 1200, margin: "0 auto" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem", marginBottom: "2rem" },
  eyebrow: { fontSize: "0.75rem", fontWeight: 700, letterSpacing: "0.12em", opacity: 0.7, marginBottom: "0.5rem" },
  title: { margin: 0, fontSize: "2rem" },
  subtitle: { marginTop: "0.5rem", opacity: 0.75 },
  button: { borderRadius: 8, padding: "0.7rem 1rem", cursor: "pointer", fontWeight: 700 },
  primaryButton: { background: "#f0c674", color: "#16120a", border: 0 },
  secondaryButton: { background: "transparent", color: "inherit", border: "1px solid currentColor" },
  panel: { border: "1px solid rgba(255,255,255,0.12)", borderRadius: 12, padding: "1.25rem", marginBottom: "1.25rem", background: "rgba(255,255,255,0.03)" },
  tableWrap: { overflowX: "auto" },
  table: { width: "100%", borderCollapse: "collapse" },
  cell: { padding: "0.85rem 0.5rem", borderBottom: "1px solid rgba(255,255,255,0.08)", textAlign: "left", verticalAlign: "top" },
  status: { display: "inline-block", padding: "0.25rem 0.5rem", borderRadius: 999, fontSize: "0.75rem", fontWeight: 700 },
  active: { background: "rgba(60,190,120,0.15)" },
  inactive: { background: "rgba(255,255,255,0.08)" },
  formGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" },
  field: { display: "flex", flexDirection: "column", gap: "0.4rem" },
  input: { width: "100%", boxSizing: "border-box", border: "1px solid rgba(255,255,255,0.16)", borderRadius: 7, padding: "0.7rem", background: "rgba(0,0,0,0.18)", color: "inherit" },
  textarea: { minHeight: 100, resize: "vertical" },
  actions: { display: "flex", gap: "0.6rem", flexWrap: "wrap", marginTop: "1rem" },
  alert: { padding: "0.8rem 1rem", borderRadius: 8, marginBottom: "1rem", background: "rgba(220,80,80,0.12)" },
  notice: { padding: "0.8rem 1rem", borderRadius: 8, marginBottom: "1rem", background: "rgba(70,170,120,0.12)" },
  warning: { padding: "0.8rem 1rem", borderRadius: 8, marginTop: "0.75rem", background: "rgba(220,170,70,0.12)" },
};

type FormState = { project_id: string; name: string; description: string; owner: string; active: boolean };
const emptyForm: FormState = { project_id: "", name: "", description: "", owner: "", active: true };

function toForm(project: ProjectRegistryProject): FormState {
  return { project_id: project.project_id, name: project.name, description: project.description, owner: project.owner ?? "", active: project.active };
}

function errorMessage(error: unknown): string {
  if (error instanceof ProjectRegistryApiError || error instanceof Error) return error.message;
  return "Unable to complete the Project Registry operation.";
}

export default function ProjectRegistryPage() {
  const [projects, setProjects] = useState<ProjectRegistryProject[]>([]);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [excelBusy, setExcelBusy] = useState(false);
  const [importMode, setImportMode] = useState<ProjectRegistryImportMode>("create_only");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setProjects(await listProjectRegistryProjects());
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void loadProjects(); }, [loadProjects]);

  function resetForm() { setForm(emptyForm); setEditingId(null); }
  function beginEdit(project: ProjectRegistryProject) {
    setNotice(null);
    setError(null);
    setForm(toForm(project));
    setEditingId(project.project_id);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = form.name.trim();
    const description = form.description.trim();
    const owner = form.owner.trim();
    if (!name) { setError("Project name is required."); return; }
    if (!editingId && !form.project_id.trim()) { setError("Project ID is required."); return; }
    setBusy(true); setError(null); setNotice(null);
    try {
      if (editingId) {
        const payload: UpdateProjectRegistryProject = { name, description, owner: owner || null, active: form.active };
        const updated = await updateProjectRegistryProject(editingId, payload);
        setProjects((current) => current.map((project) => project.project_id === updated.project_id ? updated : project));
        setNotice(`${updated.name} was updated.`);
      } else {
        const payload: CreateProjectRegistryProject = { project_id: form.project_id.trim(), name, description, owner: owner || null, active: form.active };
        const created = await createProjectRegistryProject(payload);
        setProjects((current) => [...current, created]);
        setNotice(`${created.name} was created.`);
      }
      resetForm();
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  async function handleExport() {
    setExcelBusy(true); setError(null); setNotice(null);
    try {
      const blob = await exportProjectRegistry();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "Project_Control_Registry.xlsx";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setNotice("Project Registry exported successfully.");
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setExcelBusy(false);
    }
  }

  async function handleImport(file: File | undefined) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".xlsx")) {
      setError("Only .xlsx workbooks are supported.");
      return;
    }
    if (file.size > MAX_FILE_BYTES) {
      setError("The selected workbook exceeds the 5 MB limit.");
      return;
    }
    setExcelBusy(true); setError(null); setNotice(null);
    try {
      const result = await importProjectRegistry(file, importMode);
      setNotice(`${result.imported} project${result.imported === 1 ? "" : "s"} imported (${result.mode}).`);
      await loadProjects();
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setExcelBusy(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <main style={styles.page} aria-label="Project Registry">
      <div style={styles.content}>
        <header style={styles.header}>
          <div>
            <div style={styles.eyebrow}>PROJECT CONTROL CENTER</div>
            <h1 style={styles.title}>Project Registry</h1>
            <p style={styles.subtitle}>Manage the authoritative project definitions used by Project Control.</p>
          </div>
          <button type="button" style={{ ...styles.button, ...styles.secondaryButton }} onClick={() => void loadProjects()} disabled={loading || busy || excelBusy}>
            {loading ? "Loading..." : "Refresh"}
          </button>
        </header>

        {error ? <div style={styles.alert} role="alert"><strong>Registry operation blocked.</strong><div>{error}</div></div> : null}
        {notice ? <div style={styles.notice} role="status">{notice}</div> : null}

        <section style={styles.panel} aria-label="Excel registry operations">
          <h2>Excel Registry</h2>
          <p>Export the active registry or import a validated XLSX workbook.</p>
          <div style={styles.actions}>
            <button type="button" style={{ ...styles.button, ...styles.secondaryButton }} onClick={() => void handleExport()} disabled={excelBusy || loading}>
              {excelBusy ? "Working..." : "Export Registry"}
            </button>
            <input ref={fileInputRef} type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={(event) => void handleImport(event.target.files?.[0])} disabled={excelBusy} />
          </div>
          <div style={{ ...styles.formGrid, marginTop: "1rem" }}>
            <label style={styles.field}>
              <span>Import mode</span>
              <select style={styles.input} value={importMode} onChange={(event) => setImportMode(event.target.value as ProjectRegistryImportMode)} disabled={excelBusy}>
                <option value="create_only">Create only</option>
                <option value="upsert">Upsert existing projects</option>
              </select>
            </label>
          </div>
          {importMode === "upsert" ? <div style={styles.warning}>Upsert mode updates existing authoritative projects. Use it only when the workbook is intentionally authoritative.</div> : null}
        </section>

        <section style={styles.panel} aria-label="Registered projects">
          <h2>Registered Projects</h2>
          <p>Projects returned here are sourced from the authoritative Project Registry API.</p>
          {loading ? <p role="status">Loading registered projects...</p> : projects.length === 0 ? <p>No projects are currently registered.</p> : (
            <div style={styles.tableWrap}>
              <table style={styles.table}>
                <thead><tr>{["Project", "Project ID", "Owner", "Status", "Created", "Actions"].map((heading) => <th key={heading} style={styles.cell}>{heading}</th>)}</tr></thead>
                <tbody>{projects.map((project) => <tr key={project.project_id}>
                  <td style={styles.cell}><strong>{project.name}</strong><div>{project.description || "No description."}</div></td>
                  <td style={styles.cell}><code>{project.project_id}</code></td>
                  <td style={styles.cell}>{project.owner ?? "—"}</td>
                  <td style={styles.cell}><span style={{ ...styles.status, ...(project.active ? styles.active : styles.inactive) }}>{project.active ? "Active" : "Inactive"}</span></td>
                  <td style={styles.cell}>{new Date(project.created_at).toLocaleString()}</td>
                  <td style={styles.cell}><button type="button" style={{ ...styles.button, ...styles.secondaryButton }} onClick={() => beginEdit(project)} disabled={busy || excelBusy}>Edit</button></td>
                </tr>)}</tbody>
              </table>
            </div>
          )}
        </section>

        <section style={styles.panel} aria-label="Project Registry editor">
          <h2>{editingId ? "Edit Project" : "Create Project"}</h2>
          <p>Changes are submitted to the server-authoritative Project Registry.</p>
          <form onSubmit={submit}>
            <div style={styles.formGrid}>
              <label style={styles.field}><span>Project ID</span><input style={styles.input} value={form.project_id} onChange={(event) => setForm((current) => ({ ...current, project_id: event.target.value }))} disabled={editingId !== null || busy || excelBusy} required={!editingId} maxLength={128} /></label>
              <label style={styles.field}><span>Name</span><input style={styles.input} value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} disabled={busy || excelBusy} required maxLength={255} /></label>
              <label style={styles.field}><span>Owner</span><input style={styles.input} value={form.owner} onChange={(event) => setForm((current) => ({ ...current, owner: event.target.value }))} disabled={busy || excelBusy} maxLength={255} /></label>
              <label style={{ ...styles.field, flexDirection: "row", alignItems: "center", marginTop: "1.8rem" }}><input type="checkbox" checked={form.active} onChange={(event) => setForm((current) => ({ ...current, active: event.target.checked }))} disabled={busy || excelBusy} /><span>Active</span></label>
            </div>
            <label style={{ ...styles.field, marginTop: "1rem" }}><span>Description</span><textarea style={{ ...styles.input, ...styles.textarea }} value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} disabled={busy || excelBusy} maxLength={2000} /></label>
            <div style={styles.actions}><button type="submit" style={{ ...styles.button, ...styles.primaryButton }} disabled={busy || excelBusy}>{busy ? (editingId ? "Saving..." : "Creating...") : (editingId ? "Save Changes" : "Create Project")}</button>{editingId ? <button type="button" style={{ ...styles.button, ...styles.secondaryButton }} onClick={resetForm} disabled={busy || excelBusy}>Cancel</button> : null}</div>
          </form>
        </section>
      </div>
    </main>
  );
}
