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
  /**
   * Stable governance-case identifier.
   *
   * Example:
   * CASE-E2E-003
   */
  case_id: string;

  /**
   * Authoritative Privacy Change Registry identifier.
   *
   * Example:
   * PCR-E2E-001
   */
  change_id: string;

  /**
   * Human-readable assessment title.
   */
  title: string;

  /**
   * Concise authoritative assessment summary.
   */
  summary: string;

  /**
   * Authoritative trigger information.
   *
   * The backend exposes this as a nested object rather
   * than flattened trigger_type / trigger_source /
   * triggered_at properties.
   */
  trigger: PrivacyGovernanceCaseTrigger;

  /**
   * Governance risk classification.
   */
  risk: string;

  /**
   * Authoritative processing identifiers associated
   * with the governance case.
   */
  processing_ids: string[];

  /**
   * Authoritative data-mapping identifiers associated
   * with the governance case.
   */
  data_map_ids: string[];

  /**
   * Result of automated privacy validation.
   */
  validation_status: string;

  /**
   * Email delivery status.
   */
  email_status: string;

  /**
   * Current governance lifecycle status.
   *
   * Pending:
   *   PENDING_DPO_GRC
   *
   * Completed states:
   *   APPROVED
   *   REJECTED
   *   BLOCKED
   */
  governance_status: string;

  /**
   * Final governance decision.
   *
   * Null while the case remains pending.
   */
  final_decision: string | null;

  /**
   * Timestamp of the final governance decision.
   *
   * Null while the case remains pending.
   */
  final_decision_at: string | null;

  /**
   * Authoritative governance approval/decision evidence.
   */
  approval_history: PrivacyGovernanceApprovalRecord[];
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