"use client";

/**
 * EasyChatBot CyberSecurity Operations Center.
 *
 * Reporting Workspace.
 *
 * Stakeholder sign-off:
 * Reporting Manager
 *
 * Review focus:
 * - reporting coverage;
 * - reporting status;
 * - regulatory / GRC reporting;
 * - management reporting;
 * - evidence completeness;
 * - report quality;
 * - deadlines;
 * - overdue reports;
 * - accountable ownership;
 * - governance exceptions.
 *
 * Presentation/demo layer only.
 *
 * Does NOT:
 * - submit reports;
 * - communicate with regulators;
 * - modify regulatory records;
 * - approve reports;
 * - certify evidence automatically;
 * - execute production actions.
 */

interface ReportItem {
  id: string;
  name: string;
  type: "Regulatory" | "GRC" | "Management" | "Security";
  owner: string;
  dueDate: string;
  status: "Ready" | "In Progress" | "Review" | "Overdue";
  completeness: number;
  quality: number;
  evidence: "Complete" | "Partial" | "Missing";
  priority: "Critical" | "High" | "Medium" | "Low";
}

interface ReportingMetric {
  label: string;
  value: string;
  description: string;
}

const REPORTS: ReportItem[] = [
  {
    id: "RPT-001",
    name: "Cybersecurity Risk Report",
    type: "Management",
    owner: "Security Governance",
    dueDate: "28 Aug 2026",
    status: "Review",
    completeness: 94,
    quality: 92,
    evidence: "Complete",
    priority: "High",
  },
  {
    id: "RPT-002",
    name: "AI Governance Control Report",
    type: "GRC",
    owner: "AI Governance",
    dueDate: "30 Aug 2026",
    status: "In Progress",
    completeness: 81,
    quality: 88,
    evidence: "Partial",
    priority: "High",
  },
  {
    id: "RPT-003",
    name: "Data Protection Compliance Report",
    type: "Regulatory",
    owner: "Data Protection",
    dueDate: "02 Sep 2026",
    status: "Ready",
    completeness: 98,
    quality: 96,
    evidence: "Complete",
    priority: "High",
  },
  {
    id: "RPT-004",
    name: "Third-Party Security Report",
    type: "Security",
    owner: "Third Party Risk",
    dueDate: "26 Aug 2026",
    status: "Overdue",
    completeness: 63,
    quality: 71,
    evidence: "Partial",
    priority: "Critical",
  },
  {
    id: "RPT-005",
    name: "Operational Resilience Report",
    type: "GRC",
    owner: "Operational Risk",
    dueDate: "05 Sep 2026",
    status: "In Progress",
    completeness: 76,
    quality: 83,
    evidence: "Partial",
    priority: "Medium",
  },
  {
    id: "RPT-006",
    name: "Executive Security Dashboard",
    type: "Management",
    owner: "Security Operations",
    dueDate: "01 Sep 2026",
    status: "Ready",
    completeness: 100,
    quality: 97,
    evidence: "Complete",
    priority: "Medium",
  },
];

const REPORTING_METRICS: ReportingMetric[] = [
  {
    label: "Reports Tracked",
    value: "24",
    description: "Current reporting portfolio",
  },
  {
    label: "Due This Period",
    value: "8",
    description: "Reports requiring delivery",
  },
  {
    label: "Overdue",
    value: "2",
    description: "Reports beyond target date",
  },
  {
    label: "Evidence Coverage",
    value: "91%",
    description: "Reporting evidence completeness",
  },
];

const REPORT_TYPES = [
  {
    label: "Regulatory",
    value: 6,
  },
  {
    label: "GRC",
    value: 8,
  },
  {
    label: "Management",
    value: 5,
  },
  {
    label: "Security",
    value: 5,
  },
];

const REPORT_STATUS = [
  {
    label: "Ready",
    value: 9,
  },
  {
    label: "In Progress",
    value: 8,
  },
  {
    label: "Review",
    value: 5,
  },
  {
    label: "Overdue",
    value: 2,
  },
];

function statusClass(status: ReportItem["status"]) {
  switch (status) {
    case "Ready":
      return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";

    case "In Progress":
      return "border-sky-500/40 bg-sky-500/10 text-sky-300";

    case "Review":
      return "border-purple-500/40 bg-purple-500/10 text-purple-300";

    default:
      return "border-red-500/40 bg-red-500/10 text-red-300";
  }
}

function priorityClass(priority: ReportItem["priority"]) {
  switch (priority) {
    case "Critical":
      return "border-red-500/40 bg-red-500/10 text-red-300";

    case "High":
      return "border-orange-500/40 bg-orange-500/10 text-orange-300";

    case "Medium":
      return "border-yellow-500/40 bg-yellow-500/10 text-yellow-300";

    default:
      return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
  }
}

function evidenceClass(evidence: ReportItem["evidence"]) {
  switch (evidence) {
    case "Complete":
      return "text-emerald-400";

    case "Partial":
      return "text-yellow-400";

    default:
      return "text-red-400";
  }
}

function MetricCard({
  label,
  value,
  description,
  accent = "purple",
}: {
  label: string;
  value: string;
  description: string;
  accent?: "purple" | "red" | "orange" | "green";
}) {
  const accents = {
    purple: "border-purple-500/30",
    red: "border-red-500/30",
    orange: "border-orange-500/30",
    green: "border-emerald-500/30",
  };

  return (
    <div
      className={`rounded-2xl border bg-slate-950/80 p-5 ${accents[accent]}`}
    >
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
        {label}
      </p>

      <p className="mt-2 text-3xl font-bold text-white">
        {value}
      </p>

      <p className="mt-1 text-[10px] text-slate-600">
        {description}
      </p>
    </div>
  );
}

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div>
      <p className="text-[9px] font-semibold uppercase tracking-[0.2em] text-purple-400">
        {eyebrow}
      </p>

      <h2 className="mt-1 text-lg font-semibold text-white">
        {title}
      </h2>

      <p className="mt-1 text-[10px] text-slate-500">
        {description}
      </p>
    </div>
  );
}

export default function ReportingWorkspace() {
  const overdue = REPORTS.filter(
    (report) => report.status === "Overdue",
  ).length;

  const review = REPORTS.filter(
    (report) => report.status === "Review",
  ).length;

  const ready = REPORTS.filter(
    (report) => report.status === "Ready",
  ).length;

  const averageCompleteness = Math.round(
    REPORTS.reduce(
      (total, report) => total + report.completeness,
      0,
    ) / REPORTS.length,
  );

  const averageQuality = Math.round(
    REPORTS.reduce(
      (total, report) => total + report.quality,
      0,
    ) / REPORTS.length,
  );

  return (
    <main className="space-y-8">
      {/* HEADER */}

      <header className="border-b border-slate-800 pb-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-purple-400">
              EasyChatBot CyberSecurity Operations Center
            </p>

            <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Reporting
            </h1>

            <p className="mt-2 max-w-3xl text-sm text-slate-400 sm:text-base">
              Monitor regulatory, GRC, security and management reporting
              coverage, evidence readiness, quality and deadlines.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <span className="inline-flex rounded-full border border-purple-500/40 bg-purple-500/10 px-3 py-1.5 text-xs font-semibold text-purple-300">
              DEMO ENVIRONMENT
            </span>

            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Reporting controls operational
            </span>
          </div>
        </div>
      </header>

      {/* REPORTING POSTURE */}

      <section className="grid gap-4 lg:grid-cols-[1.15fr_repeat(3,minmax(0,1fr))]">
        <div className="rounded-2xl border border-purple-500/40 bg-slate-950/80 p-5">
          <div className="flex items-center gap-5">
            <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-full border-[6px] border-purple-500/30 bg-slate-950">
              <div className="text-center">
                <p className="text-2xl font-bold text-white">
                  {averageCompleteness}%
                </p>

                <p className="text-[9px] uppercase tracking-wider text-slate-500">
                  Completeness
                </p>
              </div>
            </div>

            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-purple-400">
                Current Reporting Posture
              </p>

              <h2 className="mt-1 text-2xl font-bold text-white">
                Controlled
              </h2>

              <p className="mt-2 text-xs leading-5 text-slate-400">
                Reporting coverage is broadly controlled, with targeted
                attention required for overdue reporting and incomplete
                evidence.
              </p>
            </div>
          </div>
        </div>

        <MetricCard
          label="Reports Tracked"
          value="24"
          description="Current reporting portfolio"
        />

        <MetricCard
          label="Due This Period"
          value="8"
          description="Reports requiring delivery"
          accent="orange"
        />

        <MetricCard
          label="Overdue"
          value="2"
          description="Reports requiring attention"
          accent="red"
        />
      </section>

      {/* KEY METRICS */}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {REPORTING_METRICS.map((metric) => (
          <MetricCard
            key={metric.label}
            label={metric.label}
            value={metric.value}
            description={metric.description}
          />
        ))}
      </section>

      {/* REPORTING PORTFOLIO */}

      <section>
        <div className="mb-4 flex items-end justify-between">
          <SectionHeading
            eyebrow="Reporting Operations"
            title="Reporting Portfolio"
            description="Current reports requiring preparation, review, evidence validation or delivery."
          />

          <span className="rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 text-[10px] font-semibold text-red-300">
            {overdue} overdue
          </span>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {REPORTS.map((report) => (
            <article
              key={report.id}
              className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[9px] text-slate-600">
                      {report.id}
                    </span>

                    <span
                      className={`rounded-full border px-2 py-0.5 text-[9px] font-semibold ${priorityClass(
                        report.priority,
                      )}`}
                    >
                      {report.priority}
                    </span>

                    <span
                      className={`rounded-full border px-2 py-0.5 text-[9px] font-semibold ${statusClass(
                        report.status,
                      )}`}
                    >
                      {report.status}
                    </span>
                  </div>

                  <h3 className="mt-3 text-base font-semibold text-white">
                    {report.name}
                  </h3>

                  <p className="mt-1 text-xs text-slate-500">
                    {report.type} · {report.owner}
                  </p>
                </div>

                <div className="shrink-0 text-right">
                  <p className="text-[9px] uppercase tracking-wider text-slate-600">
                    Due
                  </p>

                  <p className="mt-1 text-xs font-semibold text-white">
                    {report.dueDate}
                  </p>
                </div>
              </div>

              {/* QUALITY */}

              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <ProgressMetric
                  label="Completeness"
                  value={report.completeness}
                />

                <ProgressMetric
                  label="Report Quality"
                  value={report.quality}
                />
              </div>

              {/* DETAILS */}

              <div className="mt-5 grid grid-cols-2 gap-4 border-t border-slate-800 pt-4 sm:grid-cols-3">
                <Detail
                  label="Evidence"
                  value={report.evidence}
                  valueClass={evidenceClass(report.evidence)}
                />

                <Detail
                  label="Owner"
                  value={report.owner}
                />

                <Detail
                  label="Type"
                  value={report.type}
                />
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* ANALYTICS */}

      <section className="grid gap-4 lg:grid-cols-3">
        {/* REPORT TYPES */}

        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5">
          <SectionHeading
            eyebrow="Reporting Analytics"
            title="Reporting Coverage"
            description="Distribution across the current reporting portfolio."
          />

          <div className="mt-6 space-y-5">
            {REPORT_TYPES.map((item) => {
              const percentage = Math.round(
                (item.value / 24) * 100,
              );

              return (
                <div key={item.label}>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">
                      {item.label}
                    </span>

                    <span className="font-semibold text-white">
                      {item.value}
                    </span>
                  </div>

                  <div className="mt-2 h-2 rounded-full bg-slate-900">
                    <div
                      className="h-2 rounded-full bg-purple-500"
                      style={{
                        width: `${percentage}%`,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* REPORT STATUS */}

        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5">
          <SectionHeading
            eyebrow="Delivery Status"
            title="Report Readiness"
            description="Current reporting workflow position."
          />

          <div className="mt-6 flex items-center justify-center">
            <div className="relative flex h-40 w-40 items-center justify-center rounded-full border-[18px] border-purple-500/20">
              <div className="absolute inset-[-18px] rounded-full border-[18px] border-transparent border-t-purple-500 border-r-emerald-400" />

              <div className="text-center">
                <p className="text-3xl font-bold text-white">
                  {Math.round((ready / 24) * 100)}%
                </p>

                <p className="text-[9px] uppercase tracking-wider text-slate-500">
                  Ready
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 space-y-3">
            {REPORT_STATUS.map((item) => (
              <div
                key={item.label}
                className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950 p-3"
              >
                <span className="text-xs text-slate-400">
                  {item.label}
                </span>

                <span className="text-sm font-semibold text-white">
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* GOVERNANCE */}

        <div className="rounded-2xl border border-purple-500/40 bg-purple-500/[0.04] p-5">
          <SectionHeading
            eyebrow="GRC Control"
            title="Reporting Governance"
            description="Reporting remains subject to accountable review and evidence validation."
          />

          <div className="mt-5 space-y-3">
            <GovernanceRow
              label="Automated submission"
              value="Disabled"
              valueClass="text-emerald-400"
            />

            <GovernanceRow
              label="Evidence validation"
              value="Required"
              valueClass="text-purple-300"
            />

            <GovernanceRow
              label="Reports in review"
              value={`${review} open`}
              valueClass="text-yellow-400"
            />

            <GovernanceRow
              label="Overdue reports"
              value={`${overdue} require action`}
              valueClass="text-red-300"
            />
          </div>

          <div className="mt-5 rounded-xl border border-purple-500/30 bg-slate-950/70 p-4">
            <p className="text-[9px] font-semibold uppercase tracking-[0.18em] text-purple-400">
              Required next step
            </p>

            <p className="mt-2 text-sm font-semibold leading-5 text-white">
              Resolve overdue reporting and complete evidence validation
              before accountable sign-off.
            </p>
          </div>
        </div>
      </section>

      {/* QUALITY ASSURANCE */}

      <section className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5">
          <SectionHeading
            eyebrow="Reporting Assurance"
            title="Quality & Evidence Coverage"
            description="Current reporting quality and supporting evidence position."
          />

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <AssuranceCard
              label="Evidence Completeness"
              value={91}
              status="Healthy"
            />

            <AssuranceCard
              label="Report Quality"
              value={averageQuality}
              status="Healthy"
            />

            <AssuranceCard
              label="Owner Assignment"
              value={96}
              status="Healthy"
            />

            <AssuranceCard
              label="Deadline Compliance"
              value={83}
              status="Review"
            />
          </div>
        </div>

        {/* CALENDAR */}

        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5">
          <SectionHeading
            eyebrow="Reporting Calendar"
            title="Upcoming Deadlines"
            description="Nearest reporting obligations requiring attention."
          />

          <div className="mt-5 space-y-3">
            {REPORTS.slice(0, 4).map((report) => (
              <div
                key={report.id}
                className="rounded-xl border border-slate-800 bg-slate-950 p-3"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs font-semibold text-white">
                    {report.name}
                  </p>

                  <span
                    className={`rounded-full border px-2 py-1 text-[9px] font-semibold ${statusClass(
                      report.status,
                    )}`}
                  >
                    {report.status}
                  </span>
                </div>

                <div className="mt-2 flex items-center justify-between">
                  <span className="text-[10px] text-slate-600">
                    {report.owner}
                  </span>

                  <span className="text-[10px] font-semibold text-slate-300">
                    {report.dueDate}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* REPORTING DECISION QUEUE */}

      <section className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5">
        <div className="flex items-end justify-between">
          <SectionHeading
            eyebrow="Operations"
            title="Reporting Decision Queue"
            description="Reports requiring review, evidence completion or management attention."
          />

          <span className="rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-[10px] font-semibold text-purple-300">
            {review + overdue} review items
          </span>
        </div>

        <div className="mt-5 overflow-hidden rounded-xl border border-slate-800">
          <div className="hidden grid-cols-[1.5fr_0.7fr_0.8fr_0.8fr_1fr] gap-4 bg-slate-900 px-4 py-3 text-[9px] font-semibold uppercase tracking-wider text-slate-500 sm:grid">
            <span>Report</span>
            <span>Priority</span>
            <span>Completeness</span>
            <span>Status</span>
            <span>Owner</span>
          </div>

          <div className="divide-y divide-slate-800">
            {REPORTS.filter(
              (report) =>
                report.status === "Review" ||
                report.status === "Overdue",
            ).map((report) => (
              <div
                key={report.id}
                className="grid gap-3 px-4 py-4 sm:grid-cols-[1.5fr_0.7fr_0.8fr_0.8fr_1fr] sm:items-center sm:gap-4"
              >
                <div>
                  <p className="text-sm font-semibold text-white">
                    {report.name}
                  </p>

                  <p className="mt-1 text-[10px] text-slate-600">
                    {report.id} · {report.type}
                  </p>
                </div>

                <span
                  className={`w-fit rounded-full border px-2 py-1 text-[9px] font-semibold ${priorityClass(
                    report.priority,
                  )}`}
                >
                  {report.priority}
                </span>

                <span className="text-sm font-semibold text-white">
                  {report.completeness}%
                </span>

                <span
                  className={`w-fit rounded-full border px-2 py-1 text-[9px] font-semibold ${statusClass(
                    report.status,
                  )}`}
                >
                  {report.status}
                </span>

                <span className="text-xs text-slate-300">
                  {report.owner}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FOOTER */}

      <footer className="flex flex-col gap-2 border-t border-slate-800 pt-5 text-[10px] text-slate-600 sm:flex-row sm:items-center sm:justify-between">
        <span>
          EasyChatBot CyberSecurity Operations Center
        </span>

        <span>
          Controlled reporting intelligence · Accountable review required ·
          Demo data
        </span>
      </footer>
    </main>
  );
}

function ProgressMetric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <p className="text-[9px] font-semibold uppercase tracking-wider text-slate-600">
          {label}
        </p>

        <p className="text-sm font-bold text-white">
          {value}%
        </p>
      </div>

      <div className="mt-2 h-2 rounded-full bg-slate-900">
        <div
          className={`h-2 rounded-full ${
            value >= 90
              ? "bg-emerald-500"
              : value >= 75
                ? "bg-purple-500"
                : "bg-orange-500"
          }`}
          style={{
            width: `${value}%`,
          }}
        />
      </div>
    </div>
  );
}

function AssuranceCard({
  label,
  value,
  status,
}: {
  label: string;
  value: number;
  status: "Healthy" | "Review";
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-white">
          {label}
        </p>

        <p className="text-lg font-bold text-white">
          {value}%
        </p>
      </div>

      <div className="mt-4 h-2 rounded-full bg-slate-900">
        <div
          className={`h-2 rounded-full ${
            status === "Healthy"
              ? "bg-emerald-500"
              : "bg-yellow-500"
          }`}
          style={{
            width: `${value}%`,
          }}
        />
      </div>

      <p
        className={`mt-2 text-[10px] font-semibold ${
          status === "Healthy"
            ? "text-emerald-400"
            : "text-yellow-400"
        }`}
      >
        {status}
      </p>
    </div>
  );
}

function Detail({
  label,
  value,
  valueClass = "text-slate-300",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div>
      <p className="text-[8px] font-semibold uppercase tracking-wider text-slate-600">
        {label}
      </p>

      <p
        className={`mt-1 truncate text-[10px] font-medium ${valueClass}`}
      >
        {value}
      </p>
    </div>
  );
}

function GovernanceRow({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: string;
  valueClass: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-3">
      <span className="text-xs text-slate-400">
        {label}
      </span>

      <span className={`text-[10px] font-semibold ${valueClass}`}>
        {value}
      </span>
    </div>
  );
}