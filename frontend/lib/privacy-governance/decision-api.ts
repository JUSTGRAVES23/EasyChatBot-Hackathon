import type {
  PrivacyGovernanceCaseDetail,
} from "./types";

export type GovernanceDecision = "approve" | "reject" | "request-changes";
export type GovernanceRole = "DPO" | "GRC";

export interface GovernanceDecisionRequest {
  change_id: string;
  approval_id: string;
  reviewer: string;
  role: GovernanceRole;
  comment: string;
}

export interface GovernanceDecisionResponse {
  case: PrivacyGovernanceCaseDetail;
  approval_record: Record<string, unknown>;
}

const API_BASE = "/api/privacy/governance";

export async function submitGovernanceDecision(
  caseId: string,
  decision: GovernanceDecision,
  request: GovernanceDecisionRequest,
  signal?: AbortSignal,
): Promise<GovernanceDecisionResponse> {
  const response = await fetch(
    `${API_BASE}/cases/${encodeURIComponent(caseId)}/${decision}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
      signal,
    },
  );

  if (!response.ok) {
    let message = `Governance decision failed (${response.status}).`;

    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Keep the stable HTTP error message when the body is not JSON.
    }

    throw new Error(message);
  }

  return (await response.json()) as GovernanceDecisionResponse;
}
