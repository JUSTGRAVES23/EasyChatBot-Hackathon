"use client";

/**
 * EasyChatBot CyberSecurity Operations Center.
 *
 * Escalations Workspace.
 *
 * Stakeholder sign-off:
 * Escalations Manager
 *
 * Review focus:
 * - open escalations;
 * - severity;
 * - escalation level;
 * - SLA performance;
 * - ageing;
 * - ownership;
 * - business impact;
 * - required decision;
 * - overdue actions;
 * - management attention.
 *
 * Presentation/demo layer only.
 *
 * Does NOT:
 * - execute remediation;
 * - modify production systems;
 * - close escalations automatically;
 * - approve risk acceptance;
 * - change incident state;
 * - bypass accountable human review.
 */

interface Escalation {
  id: string;
  title: string;
  severity: "Critical" | "High" | "Medium";
  level: "Executive" | "Management" | "Operational";
  owner: string;
  age: string;
  sla: string;
  slaStatus: "Breached" | "At Risk" | "Within SLA";
  impact: string;
  source: string;
  status: "Open" | "Investigating" | "Awaiting Decision";
  decision: string;
}

const ESCALATIONS: Escalation[] = [
  {
    id: "ESC-2026-014",
    title: "AI prompt injection campaign",
    severity: "Critical",
    level: "Executive",
    owner: "AI Security",
    age: "2h 18m",
    sla: "4h",
    slaStatus: "At Risk",
    impact: "AI application boundary",
    source: "Threat Intelligence",
    status: "Investigating",
    decision: "Confirm containment approach",
  },
  {
    id: "ESC-2026-013",
    title: "Suspicious privileged API access",
    severity: "High",
    level: "Management",
    owner: "Security Operations",
    age: "5h 42m",
    sla: "8h",
    slaStatus: "Within SLA",
    impact: "Privileged access",
    source: "Identity Monitoring",
    status: "Investigating",
    decision: "Review access controls",
  },
  {
    id: "ESC-2026-011",
    title: "Dependency vulnerability exposure",
    severity: "High",
    level: "Management",
    owner: "Technology Risk",
    age: "19h",
    sla: "24h",
    slaStatus: "At Risk",
    impact: "Application dependencies",
    source: "Vulnerability Management",
    status: "Awaiting Decision",
    decision: "Confirm remediation priority",
  },
  {
    id: "ESC-2026-009",
    title: "Data protection control exception",
    severity: "Medium",
    level: "Operational",
    owner: "Data Protection",
    age: "1d 7h",
    sla: "48h",
    slaStatus: "Within SLA",
    impact: "Privacy controls",
    source: "Compliance Monitoring",
    status: "Open",
    decision: "Validate control exception",
  },
  {
    id: "ESC-2026-006",
    title: "Third-party security review overdue",
    severity: "Medium",
    level: "Management",
    owner: "Third Party Risk",
    age: "3d 4h",
    sla: "72h",
    slaStatus: "Breached",
    impact: "External provider",
    source: "Third Party Security",
    status: "Awaiting Decision",
    decision: "Escalate supplier review",
  },
];

const SLA_SUMMARY = [
  {
    label: "Within SLA",
    value: 2,
  },
  {
    label: "At Risk",
    value: 2,
  },
  {
    label: "Breached",
    value: 1,
  },
];

function severityClass(severity: Escalation["severity"]) {
  switch (severity) {
    case "Critical":
      return "border-red-500/40 bg-red-500/10 text-red-300";

    case "High":
      return "border-orange-500/40 bg-orange-500/10 text-orange-300";

    default:
      return "border-yellow-500/40 bg-yellow-500/10 text-yellow-300";
  }
}

function slaClass(status: Escalation["slaStatus"]) {
  switch (status) {
    case "Breached":
      return "border-red-500/40 bg-red-500/10 text-red-300";

    case "At Risk":
      return "border-orange-500/40 bg-orange-500/10 text-orange-300";

    default:
      return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
  }
}

function statusClass(status: Escalation["status"]) {
  switch (status) {
    case "Awaiting Decision":
      return "border-purple-500/40 bg-purple-500/10 text-purple-300";

    case "Investigating":
      return "border-sky-500/40 bg-sky-500/10 text-sky-300";

    default:
      return "border-slate-700 bg-slate-900 text-slate-300";
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

export default function EscalationsWorkspace() {
  const openCount = ESCALATIONS.length;

  const criticalCount = ESCALATIONS.filter(
    (item) => item.severity === "Critical",
  ).length;

  const highCount = ESCALATIONS.filter(
    (item) => item.severity === "High",
  ).length;

  const breachedCount = ESCALATIONS.filter(
    (item) => item.slaStatus === "Breached",
  ).length;

  const decisionCount = ESCALATIONS.filter(
    (item) => item.status === "Awaiting Decision",
  ).length;

  const atRiskCount = ESCALATIONS.filter(
    (item) => item.slaStatus === "At Risk",
  ).length;

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
              Escalations
            </h1>

            <p className="mt-2 max-w-3xl text-sm text-slate-400 sm:text-base">
              Monitor security, risk and governance escalations requiring
              accountable investigation, management attention or decision.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <span className="inline-flex rounded-full border border-purple-500/40 bg-purple-500/10 px-3 py-1.5 text-xs font-semibold text-purple-300">
              DEMO ENVIRONMENT
            </span>

            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Escalation monitoring operational
            </span>
          </div>
        </div>
      </header>

      {/* POSTURE */}

      <section className="grid gap-4 lg:grid-cols-[1.15fr_repeat(3,minmax(0,1fr))]">
        <div className="rounded-2xl border border-purple-500/40 bg-slate-950/80 p-5">
          <div className="flex items-center gap-5">
            <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-full border-[6px] border-purple-500/30 bg-slate-950">
              <div className="text-center">
                <p className="text-2xl font-bold text-white">
                  {openCount}
                </p>

                <p className="text-[9px] uppercase tracking-wider text-slate-500">
                  Open
                </p>
              </div>
            </div>

            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-purple-400">
                Current Escalation Posture
              </p>

              <h2 className="mt-1 text-2xl font-bold text-white">
                Attention Required
              </h2>

              <p className="mt-2 text-xs leading-5 text-slate-400">
                Critical and SLA-sensitive escalations require continued
                human oversight.
              </p>
            </div>
          </div>
        </div>

        <MetricCard
          label="Critical / High"
          value={`${criticalCount} / ${highCount}`}
          description="Priority escalations"
          accent="red"
        />

        <MetricCard
          label="SLA At Risk"
          value={atRiskCount.toString()}
          description="Approaching response threshold"
          accent="orange"
        />

        <MetricCard
          label="Awaiting Decision"
          value={decisionCount.toString()}
          description="Management decision required"
          accent="purple"
        />
      </section>

      {/* KEY METRICS */}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Open Escalations"
          value={openCount.toString()}
          description="Current escalation queue"
        />

        <MetricCard
          label="SLA Breached"
          value={breachedCount.toString()}
          description="Immediate management attention"
          accent="red"
        />

        <MetricCard
          label="Management Level"
          value="3"
          description="Escalations above operational level"
          accent="orange"
        />

        <MetricCard
          label="Decision Queue"
          value={decisionCount.toString()}
          description="Items requiring accountable decision"
          accent="purple"
        />
      </section>

      {/* ACTIVE ESCALATIONS */}

      <section>
        <div className="mb-4 flex items-end justify-between">
          <SectionHeading
            eyebrow="Escalation Monitoring"
            title="Active Escalations"
            description="Prioritised cases requiring investigation, management attention or decision."
          />

          <span className="rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 text-[10px] font-semibold text-red-300">
            {criticalCount + highCount} priority
          </span>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {ESCALATIONS.map((escalation) => (
            <article
              key={escalation.id}
              className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[9px] text-slate-600">
                      {escalation.id}
                    </span>

                    <span
                      className={`rounded-full border px-2 py-0.5 text-[9px] font-semibold uppercase ${severityClass(
                        escalation.severity,
                      )}`}
                    >
                      {escalation.severity}
                    </span>

                    <span
                      className={`rounded-full border px-2 py-0.5 text-[9px] font-semibold ${statusClass(
                        escalation.status,
                      )}`}
                    >
                      {escalation.status}
                    </span>
                  </div>

                  <h3 className="mt-3 text-base font-semibold text-white">
                    {escalation.title}
                  </h3>

                  <p className="mt-1 text-xs text-slate-500">
                    {escalation.source}
                  </p>
                </div>

                <div
                  className={`shrink-0 rounded-full border px-3 py-1 text-[9px] font-semibold ${slaClass(
                    escalation.slaStatus,
                  )}`}
                >
                  {escalation.slaStatus}
                </div>
              </div>

              {/* SLA */}

              <div className="mt-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[9px] font-semibold uppercase tracking-wider text-slate-600">
                      Escalation Age
                    </p>

                    <p className="mt-1 text-sm font-semibold text-white">
                      {escalation.age}
                    </p>
                  </div>

                  <div className="text-right">
                    <p className="text-[9px] font-semibold uppercase tracking-wider text-slate-600">
                      SLA
                    </p>

                    <p className="mt-1 text-sm font-semibold text-white">
                      {escalation.sla}
                    </p>
                  </div>
                </div>

                <div className="mt-3 h-2 rounded-full bg-slate-900">
                  <div
                    className={`h-2 rounded-full ${
                      escalation.slaStatus === "Breached"
                        ? "w-full bg-red-500"
                        : escalation.slaStatus === "At Risk"
                          ? "w-[78%] bg-orange-500"
                          : "w-[48%] bg-emerald-500"
                    }`}
                  />
                </div>
              </div>

              {/* DETAILS */}

              <div className="mt-5 grid grid-cols-2 gap-4 border-t border-slate-800 pt-4 sm:grid-cols-4">
                <Detail
                  label="Level"
                  value={escalation.level}
                />

                <Detail
                  label="Owner"
                  value={escalation.owner}
                />

                <Detail
                  label="Business Impact"
                  value={escalation.impact}
                />

                <Detail
                  label="Required Decision"
                  value={escalation.decision}
                />
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* ANALYTICS */}

      <section className="grid gap-4 lg:grid-cols-3">
        {/* SLA DISTRIBUTION */}

        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5">
          <SectionHeading
            eyebrow="SLA Analytics"
            title="SLA Position"
            description="Current escalation response position."
          />

          <div className="mt-6 flex items-center justify-center">
            <div className="relative flex h-40 w-40 items-center justify-center rounded-full border-[18px] border-orange-500/20">
              <div className="absolute inset-[-18px] rounded-full border-[18px] border-transparent border-t-orange-500 border-r-red-500" />

              <div className="text-center">
                <p className="text-3xl font-bold text-white">
                  {Math.round(
                    (SLA_SUMMARY[0].value /
                      openCount) *
                      100,
                  )}
                  %
                </p>

                <p className="text-[9px] uppercase tracking-wider text-slate-500">
                  Within SLA
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 space-y-3">
            {SLA_SUMMARY.map((item) => (
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

        {/* ESCALATION LEVEL */}

        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5">
          <SectionHeading
            eyebrow="Exposure Analysis"
            title="Escalation Levels"
            description="Where escalation ownership currently sits."
          />

          <div className="mt-6 space-y-5">
            <LevelBar
              label="Executive"
              value={1}
              total={openCount}
            />

            <LevelBar
              label="Management"
              value={3}
              total={openCount}
            />

            <LevelBar
              label="Operational"
              value={1}
              total={openCount}
            />
          </div>

          <div className="mt-6 rounded-xl border border-slate-800 bg-slate-950 p-4">
            <p className="text-[9px] uppercase tracking-wider text-slate-600">
              Governance interpretation
            </p>

            <p className="mt-2 text-xs leading-5 text-slate-400">
              Management-level escalations should remain visible until
              accountable ownership confirms the required action or decision.
            </p>
          </div>
        </div>

        {/* GOVERNANCE */}

        <div className="rounded-2xl border border-purple-500/40 bg-purple-500/[0.04] p-5">
          <SectionHeading
            eyebrow="GRC Control"
            title="Escalation Governance"
            description="Human accountability remains mandatory."
          />

          <div className="mt-5 space-y-3">
            <GovernanceRow
              label="Automatic closure"
              value="Disabled"
              valueClass="text-emerald-400"
            />

            <GovernanceRow
              label="Production action"
              value="Not permitted"
              valueClass="text-emerald-400"
            />

            <GovernanceRow
              label="Decision queue"
              value={`${decisionCount} open`}
              valueClass="text-purple-300"
            />

            <GovernanceRow
              label="SLA breach"
              value={`${breachedCount} requires action`}
              valueClass="text-red-300"
            />
          </div>

          <div className="mt-5 rounded-xl border border-purple-500/30 bg-slate-950/70 p-4">
            <p className="text-[9px] font-semibold uppercase tracking-[0.18em] text-purple-400">
              Required next step
            </p>

            <p className="mt-2 text-sm font-semibold leading-5 text-white">
              Review SLA-sensitive escalations and confirm accountable
              ownership and next decision.
            </p>
          </div>
        </div>
      </section>

      {/* DECISION QUEUE */}

      <section className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5">
        <div className="flex items-end justify-between">
          <SectionHeading
            eyebrow="Operations"
            title="Management Decision Queue"
            description="Escalations requiring an accountable management decision."
          />

          <span className="rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-[10px] font-semibold text-purple-300">
            {decisionCount} awaiting decision
          </span>
        </div>

        <div className="mt-5 overflow-hidden rounded-xl border border-slate-800">
          <div className="hidden grid-cols-[1.5fr_0.7fr_0.8fr_0.9fr_1.2fr] gap-4 bg-slate-900 px-4 py-3 text-[9px] font-semibold uppercase tracking-wider text-slate-500 sm:grid">
            <span>Escalation</span>
            <span>Severity</span>
            <span>Age</span>
            <span>SLA</span>
            <span>Required Decision</span>
          </div>

          <div className="divide-y divide-slate-800">
            {ESCALATIONS.filter(
              (item) =>
                item.status === "Awaiting Decision" ||
                item.slaStatus === "Breached",
            ).map((item) => (
              <div
                key={item.id}
                className="grid gap-3 px-4 py-4 sm:grid-cols-[1.5fr_0.7fr_0.8fr_0.9fr_1.2fr] sm:items-center sm:gap-4"
              >
                <div>
                  <p className="text-sm font-semibold text-white">
                    {item.title}
                  </p>

                  <p className="mt-1 text-[10px] text-slate-600">
                    {item.id} · {item.owner}
                  </p>
                </div>

                <span
                  className={`w-fit rounded-full border px-2 py-1 text-[9px] font-semibold ${severityClass(
                    item.severity,
                  )}`}
                >
                  {item.severity}
                </span>

                <span className="text-sm font-semibold text-white">
                  {item.age}
                </span>

                <span
                  className={`w-fit rounded-full border px-2 py-1 text-[9px] font-semibold ${slaClass(
                    item.slaStatus,
                  )}`}
                >
                  {item.slaStatus}
                </span>

                <span className="text-xs text-slate-300">
                  {item.decision}
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
          Controlled escalation intelligence · Human governance required ·
          Demo data
        </span>
      </footer>
    </main>
  );
}

function Detail({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <p className="text-[8px] font-semibold uppercase tracking-wider text-slate-600">
        {label}
      </p>

      <p className="mt-1 truncate text-[10px] font-medium text-slate-300">
        {value}
      </p>
    </div>
  );
}

function LevelBar({
  label,
  value,
  total,
}: {
  label: string;
  value: number;
  total: number;
}) {
  const percentage = Math.round((value / total) * 100);

  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400">
          {label}
        </span>

        <span className="font-semibold text-white">
          {value}
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