import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import PrivacyGovernanceCaseDetail from "../../frontend/components/privacy-governance/PrivacyGovernanceCaseDetail";

const caseData = {
  case_id: "CASE-001",
  title: "New learner processing",
  summary: "Controlled privacy processing.",
  trigger_type: "NEW_PROCESSING",
  triggered_at: "2026-08-23T10:00:00Z",
  trigger_source: "Processing Registry",
  risk: "MEDIUM",
  validation_status: "PASS",
  governance_status: "APPROVED",
  final_decision: "APPROVED",
  final_decision_at: "2026-08-23T12:00:00Z",
  approval_records: [
    {
      approval_id: "APR-DPO-001",
      reviewer: "DPO Reviewer",
      role: "DPO",
      decision: "APPROVED",
      comment: "DPO approved.",
    },
    {
      approval_id: "APR-GRC-001",
      reviewer: "GRC Reviewer",
      role: "GRC",
      decision: "APPROVED",
      comment: "GRC approved.",
    },
  ],
};

describe("PrivacyGovernanceCaseDetail", () => {
  it("renders approval evidence", () => {
    render(
      <PrivacyGovernanceCaseDetail
        open
        loading={false}
        error={null}
        caseData={caseData}
        onClose={vi.fn()}
        onRetry={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "CASE-001" }),
    ).toBeInTheDocument();
    expect(screen.getByText("DPO Reviewer")).toBeInTheDocument();
    expect(screen.getByText("GRC Reviewer")).toBeInTheDocument();
    expect(screen.getByText("DPO approved.")).toBeInTheDocument();
  });

  it("renders loading state", () => {
    render(
      <PrivacyGovernanceCaseDetail
        open
        loading
        error={null}
        caseData={null}
        onClose={vi.fn()}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent(
      "Loading case details",
    );
  });

  it("renders error state and retry", () => {
    const onRetry = vi.fn();

    render(
      <PrivacyGovernanceCaseDetail
        open
        loading={false}
        error="Backend unavailable."
        caseData={null}
        onClose={vi.fn()}
        onRetry={onRetry}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Backend unavailable.");

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("closes the drawer", () => {
    const onClose = vi.fn();

    render(
      <PrivacyGovernanceCaseDetail
        open
        loading={false}
        error={null}
        caseData={caseData}
        onClose={onClose}
        onRetry={vi.fn()}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Close case detail" }),
    );

    expect(onClose).toHaveBeenCalledOnce();
  });
});
