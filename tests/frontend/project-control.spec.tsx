import "@testing-library/jest-dom/vitest";

import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ProjectControlPage from "../../app/project-control/page";

const snapshot = {
  project_id: "easychatbot",
  project_name: "EasyChatBot",
  project_status: "on_track",
  overall_progress_percent: 85,
  current_milestone: "Beta 1",
  current_workstream: "Project Control Center",
  release_readiness: "BETA READY",
  open_blockers: 0,
  open_risks: 0,
  workstreams: [
    {
      workstream_id: "pcd",
      name: "Project Control Center",
      completion_percent: 85,
      status: "healthy",
      source: "api-test",
      updated_at: null,
    },
  ],
  metrics: [],
  issues: [],
  risks: [],
  actions: [],
  milestones: [],
  sources: [
    {
      source_id: "api-test",
      name: "API Test Source",
      status: "available",
      updated_at: null,
      error: null,
    },
  ],
  generated_at: "2026-09-08T15:00:00+00:00",
};

describe("Project Control Center", () => {
  it("renders the authoritative project snapshot and tracked project card", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(JSON.stringify(snapshot), {
          status: 200,
          headers: {
            "Content-Type": "application/json",
          },
        }),
      );

    render(<ProjectControlPage />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "Loading project control data",
    );

    await waitFor(() => {
      expect(screen.getByText("EasyChatBot")).toBeInTheDocument();
    });

    expect(screen.getByText("Tracked Projects")).toBeInTheDocument();
    expect(screen.getByLabelText("EasyChatBot project")).toBeInTheDocument();
    expect(
      screen.getByText(
        "AI-powered language learning platform tracked through project delivery, milestones, workstreams, risks, blockers, and release readiness.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("ON TRACK")).toBeInTheDocument();
    expect(screen.getByText("85.0%")).toBeInTheDocument();
    expect(screen.getByText("Milestone: Beta 1")).toBeInTheDocument();
    expect(
      screen.getByText("Workstream: Project Control Center"),
    ).toBeInTheDocument();
    expect(screen.getByText("Risks: 0")).toBeInTheDocument();
    expect(screen.getByText("Blockers: 0")).toBeInTheDocument();
    expect(screen.getByText("Readiness: BETA READY")).toBeInTheDocument();

    expect(fetchMock).toHaveBeenCalledWith(
      "/project-control/projects/easychatbot",
      expect.objectContaining({
        method: "GET",
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      }),
    );

    fetchMock.mockRestore();
  });

  it("refreshes the authoritative project snapshot", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(JSON.stringify(snapshot), {
          status: 200,
          headers: {
            "Content-Type": "application/json",
          },
        }),
      );

    render(<ProjectControlPage />);

    await waitFor(() => {
      expect(screen.getByText("EasyChatBot")).toBeInTheDocument();
    });

    const refreshButton = screen.getByRole("button", {
      name: "Refresh project control data",
    });

    expect(refreshButton).toBeEnabled();

    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    fetchMock.mockRestore();
  });
});
