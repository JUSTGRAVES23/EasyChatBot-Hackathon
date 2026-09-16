import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";

import {
  MemoryRouter,
  Route,
  Routes,
} from "react-router-dom";

import {
  AuthProvider,
} from "../../src/auth/AuthProvider";

import ProtectedRoute from "../../src/auth/ProtectedRoute";

import LoginPage from "../../app/login/page";


function ProtectedTestPage() {
  return (
    <div>
      Protected content
    </div>
  );
}


function renderProtectedRoute(
  initialEntry = "/protected",
) {
  return render(
    <MemoryRouter
      initialEntries={[initialEntry]}
    >
      <AuthProvider>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <ProtectedTestPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/login"
            element={<LoginPage />}
          />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}


describe("authentication boundary", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });


  it("redirects an unauthenticated user to login", async () => {
    const fetchMock = vi.fn(
      async (
        input: RequestInfo | URL,
      ) => {
        expect(String(input)).toBe(
          "/auth/session",
        );

        return new Response(
          JSON.stringify({
            detail:
              "Authentication required.",
          }),
          {
            status: 401,
            headers: {
              "Content-Type":
                "application/json",
            },
          },
        );
      },
    );

    vi.stubGlobal(
      "fetch",
      fetchMock,
    );

    renderProtectedRoute();

    await waitFor(() => {
      expect(
        screen.getByRole("heading", {
          name: "EasyChatBot",
        }),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        "Authorized access required.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(
        "Protected content",
      ),
    ).not.toBeInTheDocument();

    expect(
      fetchMock,
    ).toHaveBeenCalledWith(
      "/auth/session",
      expect.objectContaining({
        method: "GET",
        credentials: "include",
      }),
    );
  });


  it("keeps an authenticated user on the protected route", async () => {
    const fetchMock = vi.fn(
      async () => {
        return new Response(
          JSON.stringify({
            authenticated: true,
          }),
          {
            status: 200,
            headers: {
              "Content-Type":
                "application/json",
            },
          },
        );
      },
    );

    vi.stubGlobal(
      "fetch",
      fetchMock,
    );

    renderProtectedRoute();

    await waitFor(() => {
      expect(
        screen.getByText(
          "Protected content",
        ),
      ).toBeInTheDocument();
    });

    expect(
      screen.queryByRole("heading", {
        name: "EasyChatBot",
      }),
    ).not.toBeInTheDocument();

    expect(
      fetchMock,
    ).toHaveBeenCalledWith(
      "/auth/session",
      expect.objectContaining({
        method: "GET",
        credentials: "include",
      }),
    );
  });


  it("fails closed when the session check has an unexpected error", async () => {
    const fetchMock = vi.fn(
      async () => {
        return new Response(
          JSON.stringify({
            detail:
              "Internal Server Error",
          }),
          {
            status: 500,
            headers: {
              "Content-Type":
                "application/json",
            },
          },
        );
      },
    );

    vi.stubGlobal(
      "fetch",
      fetchMock,
    );

    renderProtectedRoute();

    await waitFor(() => {
      expect(
        screen.getByRole("heading", {
          name: "EasyChatBot",
        }),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        "Authorized access required.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(
        "Protected content",
      ),
    ).not.toBeInTheDocument();
  });


  it("submits valid credentials through the existing auth API", async () => {
    const fetchMock = vi.fn(
      async (
        input: RequestInfo | URL,
        init?: RequestInit,
      ) => {
        const url = String(input);

        if (
          url === "/auth/login" &&
          init?.method === "POST"
        ) {
          return new Response(
            JSON.stringify({
              detail:
                "Login successful.",
              expires_at:
                "2026-09-12T09:00:00Z",
            }),
            {
              status: 200,
              headers: {
                "Content-Type":
                  "application/json",
              },
            },
          );
        }

        return new Response(
          JSON.stringify({
            authenticated: false,
          }),
          {
            status: 401,
            headers: {
              "Content-Type":
                "application/json",
            },
          },
        );
      },
    );

    vi.stubGlobal(
      "fetch",
      fetchMock,
    );

    render(
      <MemoryRouter
        initialEntries={[
          "/login?redirect=%2Fproject-control",
        ]}
      >
        <AuthProvider>
          <Routes>
            <Route
              path="/login"
              element={<LoginPage />}
            />

            <Route
              path="/project-control"
              element={
                <div>
                  Project Control
                </div>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );

    fireEvent.change(
      screen.getByLabelText("Email"),
      {
        target: {
          value:
            "authorized@example.com",
        },
      },
    );

    fireEvent.change(
      screen.getByLabelText("Password"),
      {
        target: {
          value: "test-password",
        },
      },
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "Sign in",
      }),
    );

    await waitFor(() => {
      expect(
        screen.getByText(
          "Project Control",
        ),
      ).toBeInTheDocument();
    });

    expect(
      fetchMock,
    ).toHaveBeenCalledWith(
      "/auth/login",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      }),
    );
  });


  it("does not expose authentication credentials in browser storage", async () => {
    const localStorageSetItem =
      vi.spyOn(
        Storage.prototype,
        "setItem",
      );

    const sessionStorageSetItem =
      vi.spyOn(
        Storage.prototype,
        "setItem",
      );

    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        return new Response(
          JSON.stringify({
            detail:
              "Login successful.",
            expires_at:
              "2026-09-12T09:00:00Z",
          }),
          {
            status: 200,
            headers: {
              "Content-Type":
                "application/json",
            },
          },
        );
      }),
    );

    render(
      <MemoryRouter
        initialEntries={["/login"]}
      >
        <AuthProvider>
          <Routes>
            <Route
              path="/login"
              element={<LoginPage />}
            />

            <Route
              path="/project-control"
              element={
                <div>
                  Project Control
                </div>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );

    fireEvent.change(
      screen.getByLabelText("Email"),
      {
        target: {
          value:
            "authorized@example.com",
        },
      },
    );

    fireEvent.change(
      screen.getByLabelText("Password"),
      {
        target: {
          value: "secret-password",
        },
      },
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "Sign in",
      }),
    );

    await waitFor(() => {
      expect(
        screen.queryByText(
          "Authorized access required.",
        ),
      ).not.toBeInTheDocument();
    });

    expect(
      localStorageSetItem,
    ).not.toHaveBeenCalled();

    expect(
      sessionStorageSetItem,
    ).not.toHaveBeenCalled();
  });
});
