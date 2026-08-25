export interface PrivacyGovernanceApprovalRecord {
  approval_id: string;
  case_id: string;
  change_id: string;
  reviewer: string;
  role: string;
  decision: string;
  comment: string;
  decided_at?: string | null;
}

export interface PrivacyGovernanceCaseTrigger {
  type: string;
  at: string;
  source: string;
}

export interface PrivacyGovernanceCaseDetail {
  case_id: string;
  change_id: string;
  title: string;
  summary: string;
  trigger: PrivacyGovernanceCaseTrigger;
  risk: string;
  processing_ids: string[];
  data_map_ids: string[];
  validation_status: string;
  email_status: string;
  governance_status: string;
  final_decision: string | null;
  final_decision_at: string | null;

  /**
   * Canonical approval evidence collection.
   */
  approval_history: PrivacyGovernanceApprovalRecord[];

  /**
   * Backward-compatible alias used by earlier frontend/API
   * fixtures. Runtime normalization maps it to approval_history.
   */
  approval_records?: PrivacyGovernanceApprovalRecord[];
}

export type PrivacyGovernanceCase =
  PrivacyGovernanceCaseDetail;

export type GovernanceFilter =
  | "ALL"
  | "PENDING_DPO_GRC"
  | "APPROVED"
  | "REJECTED"
  | "BLOCKED";

export interface PrivacyGovernanceSummary {
  total_cases: number;
  pending: number;
  approved: number;
  blocked: number;
  approval_records: number;
}

export interface PrivacyGovernanceStatusItem {
  status: string;
  count: number;
}
