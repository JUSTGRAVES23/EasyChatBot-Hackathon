import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import PrivacyGovernanceDashboard from "../../frontend/components/privacy-governance/PrivacyGovernanceDashboard";

const summary = {
  total_cases: 2,
  pending: 1,
  approved: 1,
  blocked: 0,
  approval_records: 2,
};

const statusChart = [
  { status: "PENDING_DPO_GRC", count: 1 },
  { status: "APPROVED", count: 1 },
  { status: "BLOCKED", count: 0 },
];

const cases = [
  {
    case_id: "CASE-001",
    title: "Pending case",
    summary: "Pending",
    trigger_type: "NEW_PROCESSING",
    triggered_at: "2026-08-23T10:00:00Z",
    risk: "MEDIUM",
    validation_status: "PASS",
    governance_status: "PENDING_DPO_GRC",
  },
  {
    case_id: "CASE-002",
    title: "Approved case",
    summary: "Approved",
    trigger_type: "PROCESSING_CHANGE",
    triggered_at: "2026-08-23T11:00:00Z",
    risk: "LOW",
    validation_status: "PASS",
    governance_status: "APPROVED",
  },
];

const detail = {
  ...cases[1],
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

function mockFetch() {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url.endsWith("/summary")) {
        return Promise.resolve(
          new Response(JSON.stringify(summary), { status: 200 }),
        );
      }

      if (url.endsWith("/status-chart")) {
        return Promise.resolve(
          new Response(JSON.stringify(statusChart), { status: 200 }),
        );
      }

      if (url.endsWith("/cases/CASE-002")) {
        return Promise.resolve(
          new Response(JSON.stringify(detail), { status: 200 }),
        );
      }

      if (url.endsWith("/cases")) {
        return Promise.resolve(
          new Response(JSON.stringify(cases), { status: 200 }),
        );
      }

      return Promise.resolve(new Response("Not found", { status: 404 }));
    }),
  );
}

describe("PrivacyGovernanceDashboard", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockFetch();
  });

  it("loads live KPI and case data", async () => {
    render(<PrivacyGovernanceDashboard />);

    expect(await screen.findByText("CASE-001")).toBeInTheDocument();
    expect(screen.getByText("CASE-002")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("filters cases from the KPI cards", async () => {
    render(<PrivacyGovernanceDashboard />);

    await screen.findByText("CASE-001");

    fireEvent.click(screen.getByRole("button", { name: /Approved/i }));

    expect(screen.getByText("CASE-002")).toBeInTheDocument();
    expect(screen.queryByText("CASE-001")).not.toBeInTheDocument();
  });

  it("filters cases from the status chart", async () => {
    render(<PrivacyGovernanceDashboard />);

    await screen.findByText("CASE-001");

    fireEvent.click(
      screen.getByRole("button", { name: /APPROVED.*1/i }),
    );

    expect(screen.getByText("CASE-002")).toBeInTheDocument();
    expect(screen.queryByText("CASE-001")).not.toBeInTheDocument();
  });

  it("opens the case detail drawer and displays approval evidence", async () => {
    render(<PrivacyGovernanceDashboard />);

    await screen.findByText("CASE-002");

    fireEvent.click(screen.getByRole("button", { name: "CASE-002" }));

    expect(
      await screen.findByRole("heading", { name: "CASE-002" }),
    ).toBeInTheDocument();

    expect(screen.getByText("DPO Reviewer")).toBeInTheDocument();
    expect(screen.getByText("GRC Reviewer")).toBeInTheDocument();
  });

  it("shows an API error and allows retry", async () => {
    const fetchMock = vi.fn().mockRejectedValue(
      new Error("Backend unavailable."),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<PrivacyGovernanceDashboard />);

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent("Unable to load governance data.");

    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("refreshes all dashboard datasets", async () => {
    render(<PrivacyGovernanceDashboard />);

    await screen.findByText("CASE-001");

    const fetchMock = vi.mocked(fetch);
    const initialCalls = fetchMock.mock.calls.length;

    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));

    await waitFor(() =>
      expect(fetchMock.mock.calls.length).toBeGreaterThan(initialCalls),
    );
  });
});
