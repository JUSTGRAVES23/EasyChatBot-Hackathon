import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";

import FunctionalityHealthDashboard from "../../app/components/operations-center/functionality-health/FunctionalityHealthDashboard";
import {
  resumeFunctionality,
  stopFunctionality,
} from "../../app/lib/api/functionalityHealthControls";

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

  it("shows the backend-authorised stop control and requires a reason", async () => {
    const stopSpy = vi
      .spyOn(
        await import("../../app/lib/api/functionalityHealthControls"),
        "stopFunctionality",
      )
      .mockResolvedValue({
        functionality_id: "conversation",
        environment: "adults",
        availability: "disabled",
        action: "stop",
        reason: "Operational incident",
        changed_at: "2026-09-05T08:05:00Z",
        changed_by: "operator",
      });

    render(<FunctionalityHealthDashboard />);

    await screen.findByRole("heading", {
      name: "Functionality Health",
    });

    fireEvent.click(
      screen.getByRole("row", {
        name: /AI Conversation.*AI.*Healthy.*98%.*240 ms/i,
      }),
    );

    const detailsPanel = await screen.findByRole("complementary");

    fireEvent.click(
      within(detailsPanel).getByRole("button", {
        name: "Stop functionality",
      }),
    );

    expect(
      within(detailsPanel).getByRole("textbox", {
        name: /Reason/i,
      }),
    ).toBeInTheDocument();

    expect(
      within(detailsPanel).getByRole("button", {
        name: "Confirm Stop",
      }),
    ).toBeDisabled();

    fireEvent.change(
      within(detailsPanel).getByRole("textbox", {
        name: /Reason/i,
      }),
      {
        target: {
          value: "Operational incident",
        },
      },
    );

    expect(
      within(detailsPanel).getByRole("button", {
        name: "Confirm Stop",
      }),
    ).toBeEnabled();

    fireEvent.click(
      within(detailsPanel).getByRole("button", {
        name: "Confirm Stop",
      }),
    );

    await waitFor(() => {
      expect(stopSpy).toHaveBeenCalledWith(
        "conversation",
        "adults",
        "Operational incident",
      );
    });
  });

  it("does not allow an empty stop reason", async () => {
    render(<FunctionalityHealthDashboard />);

    await screen.findByRole("heading", {
      name: "Functionality Health",
    });

    fireEvent.click(
      screen.getByRole("row", {
        name: /AI Conversation.*AI.*Healthy.*98%.*240 ms/i,
      }),
    );

    const detailsPanel = await screen.findByRole("complementary");

    fireEvent.click(
      within(detailsPanel).getByRole("button", {
        name: "Stop functionality",
      }),
    );

    expect(
      within(detailsPanel).getByRole("button", {
        name: "Confirm Stop",
      }),
    ).toBeDisabled();
  });

  it("shows a safe error when a stop is rejected", async () => {
    vi.spyOn(
      await import("../../app/lib/api/functionalityHealthControls"),
      "stopFunctionality",
    ).mockRejectedValue(new Error("Permission denied"));

    render(<FunctionalityHealthDashboard />);

    await screen.findByRole("heading", {
      name: "Functionality Health",
    });

    fireEvent.click(
      screen.getByRole("row", {
        name: /AI Conversation.*AI.*Healthy.*98%.*240 ms/i,
      }),
    );

    const detailsPanel = await screen.findByRole("complementary");

    fireEvent.click(
      within(detailsPanel).getByRole("button", {
        name: "Stop functionality",
      }),
    );

    fireEvent.change(
      within(detailsPanel).getByRole("textbox", {
        name: /Reason/i,
      }),
      {
        target: {
          value: "Operational incident",
        },
      },
    );

    fireEvent.click(
      within(detailsPanel).getByRole("button", {
        name: "Confirm Stop",
      }),
    );

    expect(
      await within(detailsPanel).findByRole("alert"),
    ).toHaveTextContent("Permission denied");
  });

  it("uses the resume control when the backend reports the functionality disabled", async () => {
    const disabledPayload = {
      ...healthPayload,
      functionalities: healthPayload.functionalities.map((item) =>
        item.functionality_id === "conversation"
          ? {
              ...item,
              availability: "disabled" as const,
            }
          : item,
      ),
    };

    vi.restoreAllMocks();

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(disabledPayload), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );

    const resumeSpy = vi
      .spyOn(
        await import("../../app/lib/api/functionalityHealthControls"),
        "resumeFunctionality",
      )
      .mockResolvedValue({
        functionality_id: "conversation",
        environment: "adults",
        availability: "enabled",
        action: "resume",
        reason: null,
        changed_at: "2026-09-05T08:05:00Z",
        changed_by: "operator",
      });

    render(<FunctionalityHealthDashboard />);

    await screen.findByRole("heading", {
      name: "Functionality Health",
    });

    fireEvent.click(
      screen.getByRole("row", {
        name: /AI Conversation.*AI.*Healthy.*98%.*240 ms/i,
      }),
    );

    const detailsPanel = await screen.findByRole("complementary");

    fireEvent.click(
      within(detailsPanel).getByRole("button", {
        name: "Resume functionality",
      }),
    );

    await waitFor(() => {
      expect(resumeSpy).toHaveBeenCalledWith(
        "conversation",
        "adults",
      );
    });
  });

  it("uses backend-authorised operational controls instead of the M1 read-only notice", async () => {
    render(<FunctionalityHealthDashboard />);

    await screen.findByRole("heading", {
      name: "Functionality Health",
    });

    expect(
      screen.queryByText(
        "M1 is read-only. Operational actions will be introduced through backend-authorised controls with confirmation and audit logging.",
      ),
    ).not.toBeInTheDocument();

    expect(
      screen.getByText("Backend-authorised operational controls"),
    ).toBeInTheDocument();
  });
});

