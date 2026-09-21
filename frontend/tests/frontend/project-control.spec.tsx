import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import ProjectControlPage from "../../app/project-control/page";
import * as projectControlApi from "../../app/lib/api/projectControl";
import * as projectRegistryApi from "../../app/lib/api/projectRegistry";

vi.mock("../../app/lib/api/projectControl", async () => {
  const actual = await vi.importActual<
    typeof import("../../app/lib/api/projectControl")
  >("../../app/lib/api/projectControl");

  return {
    ...actual,
    getProjectControlSnapshot: vi.fn(),
  };
});

vi.mock("../../app/lib/api/projectRegistry", async () => {
  const actual = await vi.importActual<
    typeof import("../../app/lib/api/projectRegistry")
  >("../../app/lib/api/projectRegistry");

  return {
    ...actual,
    listProjectRegistryProjects: vi.fn(),
  };
});

const mockedGetProjectControlSnapshot = vi.mocked(
  projectControlApi.getProjectControlSnapshot,
);

const mockedListProjectRegistryProjects = vi.mocked(
  projectRegistryApi.listProjectRegistryProjects,
);

function renderProjectControlPage() {
  return render(
    <MemoryRouter initialEntries={["/project-control"]}>
      <ProjectControlPage />
    </MemoryRouter>,
  );
}

const registryProjects: projectRegistryApi.ProjectRegistryProject[] = [
  {
    project_id: "easychatbot",
    name: "EasyChatBot",
    description: "EasyChatBot Academy project.",
    owner: "David",
    active: true,
    created_at: "2026-01-01T00:00:00Z",
  },
  {
    project_id: "12313",
    name: "Davidtest",
    description: "Davidtest project.",
    owner: "David",
    active: true,
    created_at: "2026-01-02T00:00:00Z",
  },
];

const easyChatBotSnapshot: projectControlApi.ProjectControlSnapshot = {
  project_id: "easychatbot",
  project_name: "EasyChatBot",
  project_status: "on_track",
  overall_progress_percent: 85,
  current_milestone: "D5.4-A",
  current_workstream: "Project Control",
  release_readiness: "READY",
  open_blockers: 0,
  open_risks: 0,
  workstreams: [],
  metrics: [],
  issues: [],
  risks: [],
  actions: [],
  milestones: [],
  sources: [],
  generated_at: "2026-09-17T21:00:00Z",
};

const davidTestSnapshot: projectControlApi.ProjectControlSnapshot = {
  project_id: "12313",
  project_name: "Davidtest",
  project_status: "on_track",
  overall_progress_percent: 50,
  current_milestone: "Project Control",
  current_workstream: "Project Control",
  release_readiness: "IN_PROGRESS",
  open_blockers: 0,
  open_risks: 0,
  workstreams: [],
  metrics: [],
  issues: [],
  risks: [],
  actions: [],
  milestones: [],
  sources: [],
  generated_at: "2026-09-17T21:00:00Z",
};

describe("Project Control Center", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockedListProjectRegistryProjects.mockResolvedValue(
      registryProjects,
    );

    mockedGetProjectControlSnapshot.mockImplementation(
      async (projectId: string) => {
        if (projectId === "easychatbot") {
          return easyChatBotSnapshot;
        }

        if (projectId === "12313") {
          return davidTestSnapshot;
        }

        throw new Error(
          `Unexpected project id: ${projectId}`,
        );
      },
    );
  });

  it("loads the authoritative EasyChatBot project snapshot", async () => {
    renderProjectControlPage();

    await waitFor(() => {
      expect(
        mockedListProjectRegistryProjects,
      ).toHaveBeenCalledTimes(1);
    });

    await waitFor(() => {
      expect(
        mockedGetProjectControlSnapshot,
      ).toHaveBeenCalledWith("easychatbot");
    });

    expect(
      screen.getByText("EasyChatBot"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("85.0%"),
    ).toBeInTheDocument();
  });

  it("renders all active projects from the Project Registry", async () => {
    renderProjectControlPage();

    await waitFor(() => {
      expect(
        screen.getByText("EasyChatBot"),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText("Davidtest"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Tracked Projects"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("(2)"),
    ).toBeInTheDocument();

    expect(
      mockedGetProjectControlSnapshot,
    ).toHaveBeenCalledWith("easychatbot");

    expect(
      mockedGetProjectControlSnapshot,
    ).toHaveBeenCalledWith("12313");
  });

  it("renders project navigation links for registered projects", async () => {
    renderProjectControlPage();

    await waitFor(() => {
      expect(
        screen.getByText("Davidtest"),
      ).toBeInTheDocument();
    });

    const easyChatBotLink = screen.getByRole("link", {
      name: /Open EasyChatBot project control/i,
    });

    const davidTestLink = screen.getByRole("link", {
      name: /Open Davidtest project control/i,
    });

    expect(easyChatBotLink).toHaveAttribute(
      "href",
      "/project-control/projects/easychatbot",
    );

    expect(davidTestLink).toHaveAttribute(
      "href",
      "/project-control/projects/12313",
    );
  });

  it("refreshes Project Registry and Project Control data", async () => {
    renderProjectControlPage();

    await waitFor(() => {
      expect(
        screen.getByText("EasyChatBot"),
      ).toBeInTheDocument();
    });

    const initialRegistryCalls =
      mockedListProjectRegistryProjects.mock.calls.length;

    const initialSnapshotCalls =
      mockedGetProjectControlSnapshot.mock.calls.length;

    const refreshButton = screen.getByRole("button", {
      name: /refresh project control data/i,
    });

    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(
        mockedListProjectRegistryProjects.mock.calls.length,
      ).toBeGreaterThan(initialRegistryCalls);
    });

    await waitFor(() => {
      expect(
        mockedGetProjectControlSnapshot.mock.calls.length,
      ).toBeGreaterThan(initialSnapshotCalls);
    });
  });

  it("handles Project Registry failure without crashing", async () => {
    mockedListProjectRegistryProjects.mockRejectedValueOnce(
      new Error("Project Registry unavailable"),
    );

    renderProjectControlPage();

    await waitFor(() => {
      expect(
        screen.getByRole("alert"),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText("Project intelligence unavailable"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Unable to load Project Registry data."),
    ).toBeInTheDocument();

    expect(
      mockedGetProjectControlSnapshot,
    ).not.toHaveBeenCalled();
  });

  it("keeps the portfolio visible when one project snapshot fails", async () => {
    mockedGetProjectControlSnapshot.mockImplementation(
      async (projectId: string) => {
        if (projectId === "easychatbot") {
          return easyChatBotSnapshot;
        }

        throw new Error("Davidtest snapshot unavailable");
      },
    );

    renderProjectControlPage();

    await waitFor(() => {
      expect(
        screen.getByText("EasyChatBot"),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText("Davidtest"),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Snapshot: Project Control snapshot unavailable.",
      ),
    ).toBeInTheDocument();
  });
});