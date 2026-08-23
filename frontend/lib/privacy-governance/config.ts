export const PRIVACY_GOVERNANCE_API_BASE =
  import.meta.env.VITE_PRIVACY_GOVERNANCE_API_BASE ??
  "/api/privacy/governance";

export const privacyGovernanceEndpoints = {
  summary: `${PRIVACY_GOVERNANCE_API_BASE}/summary`,
  statusChart: `${PRIVACY_GOVERNANCE_API_BASE}/status-chart`,
  cases: `${PRIVACY_GOVERNANCE_API_BASE}/cases`,
  caseDetail: (caseId: string) =>
    `${PRIVACY_GOVERNANCE_API_BASE}/cases/${encodeURIComponent(caseId)}`,
} as const;
