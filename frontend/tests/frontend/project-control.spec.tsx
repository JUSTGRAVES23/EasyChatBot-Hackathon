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
  generated_at:
    "2026-09-08T15:00:00+00:00",
};

describe(
  "Project Control Center",
  () => {
    it(
      "renders the authoritative project snapshot",
      async () => {
        const fetchMock =
          vi
            .spyOn(globalThis, "fetch")
            .mockResolvedValue(
              new Response(
                JSON.stringify(snapshot),
                {
                  status: 200,
                  headers: {
                    "Content-Type":
                      "application/json",
                  },
                },
              ),
            );

        render(
          <ProjectControlPage />,
        );

        expect(
          screen.getByRole(
            "status",
          ),
        ).toHaveTextContent(
          "Loading project control data",
        );

        await waitFor(() => {
          expect(
            screen.getByText(
              "EasyChatBot",
            ),
          ).toBeInTheDocument();
        });

        expect(
          screen.getByText(
            "ON TRACK",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "85.0%",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "BETA READY",
          ),
        ).toBeInTheDocument();

        expect(
          fetchMock,
        ).toHaveBeenCalledWith(
          "/project-control/projects/easychatbot",
          expect.objectContaining({
            method: "GET",
            credentials: "include",
          }),
        );

        fetchMock.mockRestore();
      },
    );

    it(
      "shows an API failure and provides retry",
      async () => {
        const fetchMock =
          vi
            .spyOn(globalThis, "fetch")
            .mockRejectedValue(
              new Error(
                "Network failure",
              ),
            );

        render(
          <ProjectControlPage />,
        );

        await waitFor(() => {
          expect(
            screen.getByRole(
              "alert",
            ),
          ).toBeInTheDocument();
        });

        expect(
          screen.getByText(
            "Unable to load Project Control data.",
          ),
        ).toBeInTheDocument();

        const retryButton =
          screen.getByRole(
            "button",
            {
              name: "Retry",
            },
          );

        fireEvent.click(
          retryButton,
        );

        await waitFor(() => {
          expect(
            fetchMock,
          ).toHaveBeenCalledTimes(2);

          expect(
            screen.getByRole(
              "alert",
            ),
          ).toHaveTextContent(
            "Unable to load Project Control data.",
          );
        });

        fetchMock.mockRestore();
      },
    );

    it(
      "shows unavailable source information",
      async () => {
        const degradedSnapshot = {
          ...snapshot,
          sources: [
            {
              ...snapshot.sources[0],
              status: "unavailable",
              error:
                "Source unavailable",
            },
          ],
        };

        const fetchMock =
          vi
            .spyOn(globalThis, "fetch")
            .mockResolvedValue(
              new Response(
                JSON.stringify(
                  degradedSnapshot,
                ),
                {
                  status: 200,
                  headers: {
                    "Content-Type":
                      "application/json",
                  },
                },
              ),
            );

        render(
          <ProjectControlPage />,
        );

        const warning =
          await screen.findByRole(
            "status",
            {
              name: "Source warning",
            },
          );

        expect(
          warning,
        ).toHaveTextContent(
          "Some project-control sources are unavailable or stale.",
        );

        const sourceName =
          screen.getByText(
            "API Test Source",
          );

        const sourceRow =
          sourceName.closest("li");

        if (!sourceRow) {
          throw new Error(
            "Expected API Test Source to be rendered inside a list item.",
          );
        }

        expect(
          sourceRow,
        ).toHaveTextContent(
          "Unavailable",
        );

        expect(
          sourceRow,
        ).toHaveTextContent(
          "Source unavailable",
        );

        fetchMock.mockRestore();
      },
    );
  },
);