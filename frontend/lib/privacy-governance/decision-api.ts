import type {
  PrivacyGovernanceCaseDetail,
} from "./types";

export type GovernanceDecision =
  | "approve"
  | "reject"
  | "request-changes";

export type GovernanceRole =
  | "DPO"
  | "GRC";

export interface GovernanceDecisionRequest {
  change_id: string;
  approval_id: string;
  reviewer: string;
  role: GovernanceRole;
  comment: string;
}

export interface GovernanceExcelSyncResult {
  status: string;
  workbook_path?: string | null;
  error?: string | null;
}

export interface GovernanceDecisionResponse {
  case: PrivacyGovernanceCaseDetail;
  approval_record: Record<string, unknown>;
  excel_sync?: GovernanceExcelSyncResult;
}

const API_BASE = "/api/privacy/governance";

export async function submitGovernanceDecision(
  caseId: string,
  decision: GovernanceDecision,
  request: GovernanceDecisionRequest,
  signal?: AbortSignal,
): Promise<GovernanceDecisionResponse> {
  const normalizedCaseId = caseId.trim();

  if (!normalizedCaseId) {
    throw new Error("Governance case ID is required.");
  }

  if (!request.change_id.trim()) {
    throw new Error("Privacy change ID is required.");
  }

  if (!request.approval_id.trim()) {
    throw new Error("Approval ID is required.");
  }

  if (!request.reviewer.trim()) {
    throw new Error("Reviewer is required.");
  }

  if (!request.comment.trim()) {
    throw new Error("Decision comment is required.");
  }

  if (request.role !== "DPO" && request.role !== "GRC") {
    throw new Error("Governance role must be DPO or GRC.");
  }

  const response = await fetch(
    `${API_BASE}/cases/${encodeURIComponent(normalizedCaseId)}/${decision}`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        change_id: request.change_id.trim(),
        approval_id: request.approval_id.trim(),
        reviewer: request.reviewer.trim(),
        role: request.role,
        comment: request.comment.trim(),
      }),
      signal,
    },
  );

  if (!response.ok) {
    let message = `Governance decision failed (${response.status}).`;

    try {
      const payload = (await response.json()) as {
        detail?: string;
        message?: string;
      };

      if (typeof payload.detail === "string" && payload.detail.trim()) {
        message = payload.detail;
      } else if (
        typeof payload.message === "string" &&
        payload.message.trim()
      ) {
        message = payload.message;
      }
    } catch {
      // Preserve stable HTTP error when response is not JSON.
    }

    throw new Error(message);
  }

  return (await response.json()) as GovernanceDecisionResponse;
}