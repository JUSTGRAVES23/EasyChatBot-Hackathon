import OperationsCenterShell from "../../components/operations-center/OperationsCenterShell";

type Workflow = {
  id: string;
  name: string;
  category: string;
  schedule: string;
  operational_status: string;
  next_run: string | null;
};

type ApiResponse = {
  scheduler: { running: boolean };
  provider: { status: string };
  workflows: Workflow[];
  count: number;
};

const API_BASE = "http://127.0.0.1:8000";

async function loadData(): Promise<ApiResponse> {
  const response = await fetch(
    `${API_BASE}/api/operations-center/email-workflows`,
    { cache: "no-store" },
  );
  if (!response.ok) throw new Error("Unable to load email workflow status.");
  return response.json();
}

export default async function EmailWorkflowsPage() {
  let data: ApiResponse | null = null;
  try {
    data = await loadData();
  } catch {
    data = null;
  }

  return (
    <OperationsCenterShell>
      <main className="min-h-screen bg-slate-50 p-8">
        <div className="mx-auto max-w-[1500px]">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Operations Control
          </p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Email Workflows
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Read-only visibility of scheduled email workflows and provider readiness.
          </p>

          {!data ? (
            <div className="mt-8 rounded-2xl border border-red-200 bg-white p-6 text-sm text-red-700 shadow-sm">
              Unable to load email workflow status.
            </div>
          ) : (
            <>
              <section className="mt-8 grid gap-4 md:grid-cols-3">
                <Metric label="Scheduler" value={data.scheduler.running ? "Running" : "Stopped"} />
                <Metric label="Workflows" value={String(data.count)} />
                <Metric label="Email Provider" value={data.provider.status} />
              </section>

              <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-200 px-6 py-4">
                  <h2 className="font-semibold text-slate-900">Scheduled Workflows</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-left text-sm">
                    <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                      <tr>
                        <th className="px-6 py-4">Workflow</th>
                        <th className="px-6 py-4">Category</th>
                        <th className="px-6 py-4">Schedule</th>
                        <th className="px-6 py-4">Status</th>
                        <th className="px-6 py-4">Next Run</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {data.workflows.map((workflow) => (
                        <tr key={workflow.id}>
                          <td className="px-6 py-4">
                            <div className="font-semibold text-slate-900">{workflow.name}</div>
                            <div className="mt-1 font-mono text-xs text-slate-400">{workflow.id}</div>
                          </td>
                          <td className="px-6 py-4 text-slate-600">{workflow.category}</td>
                          <td className="px-6 py-4 text-slate-600">{workflow.schedule}</td>
                          <td className="px-6 py-4">
                            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                              {workflow.operational_status}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-slate-600">
                            {workflow.next_run
                              ? new Date(workflow.next_run).toLocaleString()
                              : "Not scheduled"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="border-t border-slate-200 bg-slate-50 px-6 py-4 text-xs text-slate-500">
                  Read-only operational view. Workflow STOP/START controls are intentionally not exposed in M1.3.
                </div>
              </section>
            </>
          )}
        </div>
      </main>
    </OperationsCenterShell>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-2 text-2xl font-bold text-slate-900">{value}</div>
    </div>
  );
}
