import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";

import FunctionalityHealthDashboard from "../../app/components/operations-center/functionality-health/FunctionalityHealthDashboard";

const healthPayload = {
  generated_at: "2026-09-05T08:00:00Z",
  environment: "adults" as const,
  platform_health: "healthy" as const,
  platform_health_score: 96,
  user_impact: "LOW" as const,
  counts: {
    healthy: 11,
    degraded: 2,
    incident: 1,
    maintenance: 0,
    disabled: 0,
    unknown: 0,
  },
  functionalities: [
    {
      functionality_id: "conversation",
      name: "AI Conversation",
      category: "AI",
      description: "Core AI conversation capability.",
      status: "healthy" as const,
      health_score: 98,
      latency_ms: 240,
      provider: "openai",
      model: "gpt-5-mini",
      capability: "conversation",
      checked_at: "2026-09-05T08:00:00Z",
      controllable: true,
      risk_level: "low",
      reason: "Operating normally.",
    },
    {
      functionality_id: "voice_tts",
      name: "Voice / TTS",
      category: "AI",
      description: "Text-to-speech capability.",
      status: "degraded" as const,
      health_score: 72,
      latency_ms: 1800,
      provider: "openai",
      model: "tts",
      capability: "voice_tts",
      checked_at: "2026-09-05T08:00:00Z",
      controllable: true,
      risk_level: "medium",
      reason: "Provider latency above threshold.",
    },
  ],
  attention: [],
};

describe("Functionality Health", () => {
  beforeEach(() => {
    vi.restoreAllMocks();

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(healthPayload), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );
  });

  it("renders the professional Functionality Health dashboard", async () => {
    render(<FunctionalityHealthDashboard />);

    expect(
      await screen.findByRole("heading", {
        name: "Functionality Health",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Real-time operational health across all EasyChatBot capabilities.",
      ),
    ).toBeInTheDocument();

    expect(screen.getByText("Platform Health")).toBeInTheDocument();
    expect(screen.getByText("Functionality Status")).toBeInTheDocument();
    expect(screen.getByText("Status by Category")).toBeInTheDocument();
    expect(screen.getByText("Functionality Overview")).toBeInTheDocument();
  });

  it("renders live health data from the API", async () => {
    render(<FunctionalityHealthDashboard />);

    await screen.findByRole("heading", {
      name: "Functionality Health",
    });

    expect(screen.getByText("96%")).toBeInTheDocument();

    const table = screen.getByRole("table");

    expect(
      within(table).getByText("AI Conversation"),
    ).toBeInTheDocument();

    expect(
      within(table).getByText("Voice / TTS"),
    ).toBeInTheDocument();

    expect(within(table).getByText("98%")).toBeInTheDocument();
    expect(within(table).getByText("72%")).toBeInTheDocument();
    expect(within(table).getByText("240 ms")).toBeInTheDocument();
    expect(within(table).getByText("1800 ms")).toBeInTheDocument();

    const conversationRow = within(table).getByRole("row", {
      name: /AI Conversation.*AI.*Healthy.*98%.*240 ms/i,
    });

    const voiceRow = within(table).getByRole("row", {
      name: /Voice \/ TTS.*AI.*Degraded.*72%.*1800 ms/i,
    });

    expect(
      within(conversationRow).getByText("openai"),
    ).toBeInTheDocument();

    expect(
      within(voiceRow).getByText("openai"),
    ).toBeInTheDocument();
  });

  it("allows an operator to inspect a functionality by selecting its row", async () => {
    render(<FunctionalityHealthDashboard />);

    await screen.findByRole("heading", {
      name: "Functionality Health",
    });

    const table = screen.getByRole("table");

    const voiceRow = within(table).getByRole("row", {
      name: /Voice \/ TTS.*AI.*Degraded.*72%.*1800 ms/i,
    });

    fireEvent.click(voiceRow);

    const detailsPanel = await screen.findByRole("complementary");

    expect(
      within(detailsPanel).getByRole("heading", {
        name: "Voice / TTS",
      }),
    ).toBeInTheDocument();

    expect(
      within(detailsPanel).getByText("Text-to-speech capability."),
    ).toBeInTheDocument();

    expect(
      within(detailsPanel).getByText("voice_tts"),
    ).toBeInTheDocument();

    expect(
      within(detailsPanel).getByText("tts"),
    ).toBeInTheDocument();

    expect(
      within(detailsPanel).getByText(
        "Provider latency above threshold.",
      ),
    ).toBeInTheDocument();
  });

  it("refreshes the health data when Refresh is clicked", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(healthPayload), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );

    render(<FunctionalityHealthDashboard />);

    await screen.findByRole("heading", {
      name: "Functionality Health",
    });

    const initialCallCount = fetchSpy.mock.calls.length;

    fireEvent.click(
      screen.getByRole("button", {
        name: "Refresh",
      }),
    );

    await waitFor(() => {
      expect(fetchSpy.mock.calls.length).toBeGreaterThan(
        initialCallCount,
      );
    });

    expect(fetchSpy).toHaveBeenLastCalledWith(
      "/api/operations-center/functionality-health?environment=adults",
      {
        headers: {
          Accept: "application/json",
        },
      },
    );
  });

  it("shows an accessible error when the health API fails", async () => {
    vi.restoreAllMocks();

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("Service unavailable", {
        status: 503,
      }),
    );

    render(<FunctionalityHealthDashboard />);

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent(
      "Functionality health API failed: 503",
    );
  });

  it("keeps the M1 dashboard read-only", async () => {
    render(<FunctionalityHealthDashboard />);

    await screen.findByRole("heading", {
      name: "Functionality Health",
    });

    expect(
      screen.getByText(
        "M1 is read-only. Operational actions will be introduced through backend-authorised controls with confirmation and audit logging.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Read-only operational visibility"),
    ).toBeInTheDocument();

    const buttons = screen.getAllByRole("button");

    expect(
      buttons.some((button) =>
        /stop|restart|reroute|modify/i.test(
          button.textContent ?? "",
        ),
      ),
    ).toBe(false);
  });
});

