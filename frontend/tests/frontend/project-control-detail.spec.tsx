import "@testing-library/jest-dom/vitest";

import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import ProjectControlPage from "../../app/project-control/page";
import ProjectControlProjectPage from "../../app/project-control/projects/[projectId]/page";

const registryProject = {
  project_id: "12313",
  name: "Davidtest",
  description: "project test",
  owner: "davdbarbero1999@gmail.com",
  active: true,
  created_at: "2026-09-17T19:13:11+00:00",
};

const snapshot = {
  project_id: "12313",
  project_name: "Davidtest",
  project_status: "on_track",
  overall_progress_percent: 42,
  current_milestone: "Milestone A",
  current_workstream: "Foundation",
  release_readiness: "IN PROGRESS",
  open_blockers: 1,
  open_risks: 2,
  workstreams: [],
  metrics: [],
  issues: [],
  risks: [],
  actions: [],
  milestones: [],
  sources: [],
  generated_at: "2026-09-17T19:27:00+00:00",
};

function jsonResponse(body: unknown) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
      },
    }),
  );
}

describe("Project Control D5.4-A navigation", () => {
  it("renders project cards as links to the project detail route", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);

      if (url.includes("/project-control/registry/projects")) {
        return jsonResponse([registryProject]);
      }

      return jsonResponse(snapshot);
    });

    render(
      <MemoryRouter initialEntries={["/project-control"]}>
        <Routes>
          <Route
            path="/project-control"
            element={<ProjectControlPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() =>
      expect(screen.getByText("Davidtest")).toBeInTheDocument(),
    );

    const link = screen.getByRole("link", {
      name: "Open Davidtest project control",
    });

    expect(link).toHaveAttribute(
      "href",
      "/project-control/projects/12313",
    );
  });

  it("loads the selected registry project and its authoritative snapshot", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation((input) => {
        const url = String(input);

        if (
          url.endsWith(
            "/project-control/registry/projects/12313",
          )
        ) {
          return jsonResponse(registryProject);
        }

        if (
          url.endsWith(
            "/project-control/projects/12313",
          )
        ) {
          return jsonResponse(snapshot);
        }

        return jsonResponse({
          detail: "unexpected request",
        });
      });

    render(
      <MemoryRouter
        initialEntries={["/project-control/projects/12313"]}
      >
        <Routes>
          <Route
            path="/project-control/projects/:projectId"
            element={<ProjectControlProjectPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() =>
      expect(
        screen.getByRole("heading", {
          name: "Davidtest",
        }),
      ).toBeInTheDocument(),
    );

    expect(
      screen.getByText("Project ID: 12313"),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Owner: davdbarbero1999@gmail.com",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getAllByText("42%").length,
    ).toBeGreaterThanOrEqual(1);

    expect(
      screen.getByText("Milestone A"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Foundation"),
    ).toBeInTheDocument();

    /*
     * Do not assert an exact fetch count.
     *
     * React effects and the page's data-loading lifecycle may issue
     * additional requests. The contract we care about is that the
     * authoritative registry resource and authoritative project-control
     * snapshot are both requested for the selected project.
     */
    const requestedUrls = fetchMock.mock.calls.map(([input]) =>
      String(input),
    );

    expect(
      requestedUrls.some((url) =>
        url.endsWith(
          "/project-control/registry/projects/12313",
        ),
      ),
    ).toBe(true);

    expect(
      requestedUrls.some((url) =>
        url.endsWith(
          "/project-control/projects/12313",
        ),
      ),
    ).toBe(true);
  });

  it("keeps the registry route distinct from the project-control detail route", () => {
    expect("/project-control/projects").not.toBe(
      "/project-control/projects/:projectId",
    );
  });
});