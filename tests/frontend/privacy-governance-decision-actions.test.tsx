import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PrivacyGovernanceDecisionActions } from "../../frontend/components/privacy-governance/PrivacyGovernanceDecisionActions";

const submitDecision = vi.fn();

vi.mock("../../frontend/lib/privacy-governance/decision-api", () => ({
  submitGovernanceDecision: (...args: unknown[]) =>
    submitDecision(...args),
}));

describe("PrivacyGovernanceDecisionActions", () => {
  beforeEach(() => {
    submitDecision.mockReset();
    submitDecision.mockResolvedValue({
      case: {
        case_id: "CASE-6G-001",
        title: "Test",
        summary: "Test",
        governance_status: "PENDING_DPO_GRC",
        approval_records: [],
      },
      approval_record: {
        decision: "APPROVED",
      },
    });
  });

  it("requires confirmation before posting an approval", async () => {
    const onDecisionCompleted = vi.fn();

    render(
      <PrivacyGovernanceDecisionActions
        caseDetail={{
          case_id: "CASE-6G-001",
          change_id: "PCR-6G-001",
          title: "Test case",
          summary: "Test summary",
          governance_status: "PENDING_DPO_GRC",
          approval_records: [],
        }}
        onDecisionCompleted={onDecisionCompleted}
      />,
    );

    fireEvent.change(
      screen.getByPlaceholderText("Enter reviewer name"),
      { target: { value: "DPO Reviewer" } },
    );

    fireEvent.change(
      screen.getByPlaceholderText(
        "Record the rationale for this decision",
      ),
      { target: { value: "Approved after review." } },
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "Approve as DPO",
      }),
    );

    expect(
      screen.getByRole("dialog"),
    ).toBeInTheDocument();

    expect(submitDecision).not.toHaveBeenCalled();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Confirm decision",
      }),
    );

    await waitFor(() => {
      expect(submitDecision).toHaveBeenCalledTimes(1);
    });

    expect(submitDecision.mock.calls[0][0]).toBe(
      "CASE-6G-001",
    );
    expect(submitDecision.mock.calls[0][1]).toBe(
      "approve",
    );
    expect(
      submitDecision.mock.calls[0][2].role,
    ).toBe("DPO");

    expect(onDecisionCompleted).toHaveBeenCalled();
  });

  it("shows an API error without closing the decision workflow", async () => {
    submitDecision.mockRejectedValueOnce(
      new Error("Reviewer is not authorised."),
    );

    render(
      <PrivacyGovernanceDecisionActions
        caseDetail={{
          case_id: "CASE-6G-002",
          change_id: "PCR-6G-002",
          title: "Test case",
          summary: "Test summary",
          governance_status: "PENDING_DPO_GRC",
          approval_records: [],
        }}
        onDecisionCompleted={vi.fn()}
      />,
    );

    fireEvent.change(
      screen.getByPlaceholderText("Enter reviewer name"),
      { target: { value: "Reviewer" } },
    );

    fireEvent.change(
      screen.getByPlaceholderText(
        "Record the rationale for this decision",
      ),
      { target: { value: "Decision comment." } },
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "Reject",
      }),
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "Confirm decision",
      }),
    );

    await waitFor(() => {
      expect(
        screen.getByRole("alert"),
      ).toHaveTextContent(
        "Reviewer is not authorised.",
      );
    });
  });
});
