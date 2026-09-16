import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import RiskIntelligenceDashboard from "../../app/operations-center/risk-intelligence/RiskIntelligenceDashboard";
import { getRiskIntelligence } from "../../app/lib/api/riskIntelligence";

vi.mock("../../app/lib/api/riskIntelligence", () => ({
  getRiskIntelligence: vi.fn(),
}));

const mockedGetRiskIntelligence = vi.mocked(getRiskIntelligence);

describe("RiskIntelligenceDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders authoritative available metrics", async () => {
    mockedGetRiskIntelligence.mockResolvedValue({
      lifecycle_id: "CMP-2026-2028",
      as_of: "2026-09-06T12:00:00Z",
      population_status: "AVAILABLE",
      total_item_years: {
        value: 44,
        availability: "AVAILABLE",
      },
      distinct_controls: {
        value: 17,
        availability: "AVAILABLE",
      },
      distinct_domains: {
        value: 16,
        availability: "AVAILABLE",
      },
      yearly_population: {
        2026: 10,
        2027: 17,
        2028: 17,
      },
      risk_distribution: {
        HIGH: 41,
        MEDIUM: 2,
        LOW: 1,
      },
      domain_distribution: {
        "AI Governance": 6,
        "Access Control": 3,
      },
      source: "CMPMonitoringPlanItemModel + CMPControlModel",
    });

    render(<RiskIntelligenceDashboard />);

    expect(
      screen.getByText("Loading Risk Intelligence…"),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("44")).toBeInTheDocument();
    });

    expect(screen.getByText("17")).toBeInTheDocument();
    expect(screen.getByText("16")).toBeInTheDocument();
    expect(screen.getByText("2026: 10")).toBeInTheDocument();
    expect(screen.getByText("HIGH: 41")).toBeInTheDocument();
    expect(screen.getByText("AI Governance: 6")).toBeInTheDocument();
  });

  it("does not convert unavailable metrics into zero", async () => {
    mockedGetRiskIntelligence.mockResolvedValue({
      lifecycle_id: "CMP-2026-2028",
      as_of: "2026-09-06T12:00:00Z",
      population_status: "NOT_AVAILABLE",
      total_item_years: {
        value: null,
        availability: "NOT_AVAILABLE",
      },
      distinct_controls: {
        value: null,
        availability: "NOT_AVAILABLE",
      },
      distinct_domains: {
        value: null,
        availability: "NOT_AVAILABLE",
      },
      yearly_population: {},
      risk_distribution: {},
      domain_distribution: {},
      source: "CMPMonitoringPlanItemModel + CMPControlModel",
    });

    render(<RiskIntelligenceDashboard />);

    await waitFor(() => {
      expect(screen.getAllByText("Not available").length).toBeGreaterThan(0);
    });

    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("shows a retry action when the API fails", async () => {
    mockedGetRiskIntelligence.mockRejectedValue(
      new Error("Risk Intelligence is temporarily unavailable."),
    );

    render(<RiskIntelligenceDashboard />);

    await waitFor(() => {
      expect(
        screen.getByRole("alert"),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText("Risk Intelligence is temporarily unavailable."),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Retry" }),
    ).toBeInTheDocument();
  });
});
