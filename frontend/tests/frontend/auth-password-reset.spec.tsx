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
import { beforeEach, describe, expect, it, vi } from "vitest";

import ForgotPasswordPage from "../../app/forgot-password/page";
import ResetPasswordPage from "../../app/reset-password/page";
import * as authApi from "../../src/auth/authApi";

vi.mock("../../src/auth/authApi", async () => {
  const actual = await vi.importActual<
    typeof import("../../src/auth/authApi")
  >("../../src/auth/authApi");

  return {
    ...actual,
    requestPasswordReset: vi.fn(),
    confirmPasswordReset: vi.fn(),
  };
});

const requestPasswordResetMock =
  vi.mocked(authApi.requestPasswordReset);

const confirmPasswordResetMock =
  vi.mocked(authApi.confirmPasswordReset);

describe("password reset frontend workflow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("submits the forgot-password email request", async () => {
    requestPasswordResetMock.mockResolvedValue({
      detail:
        "If an account exists for that email address, a password reset email has been sent.",
    });

    render(
      <MemoryRouter initialEntries={["/forgot-password"]}>
        <Routes>
          <Route
            path="/forgot-password"
            element={<ForgotPasswordPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    const emailInput = screen.getByLabelText(/email/i);

    fireEvent.change(emailInput, {
      target: {
        value: "user@example.com",
      },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: /send me a reset link/i,
      }),
    );

    await waitFor(() => {
      expect(requestPasswordResetMock).toHaveBeenCalledWith({
        email: "user@example.com",
      });
    });

    expect(
      screen.getByText(
        /if an easychatbot account exists for that email/i,
      ),
    ).toBeInTheDocument();
  });

  it("does not expose whether an email address exists", async () => {
    requestPasswordResetMock.mockResolvedValue({
      detail:
        "If an account exists for that email address, a password reset email has been sent.",
    });

    render(
      <MemoryRouter initialEntries={["/forgot-password"]}>
        <Routes>
          <Route
            path="/forgot-password"
            element={<ForgotPasswordPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    fireEvent.change(
      screen.getByLabelText(/email/i),
      {
        target: {
          value: "unknown@example.com",
        },
      },
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: /send me a reset link/i,
      }),
    );

    await waitFor(() => {
      expect(
        screen.getByText(
          /if an easychatbot account exists for that email/i,
        ),
      ).toBeInTheDocument();
    });

    expect(
      screen.queryByText(/account does not exist/i),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByText(/email not found/i),
    ).not.toBeInTheDocument();
  });

  it("renders the reset form when a token is present", () => {
    render(
      <MemoryRouter
        initialEntries={[
          "/reset-password?token=test-reset-token",
        ]}
      >
        <Routes>
          <Route
            path="/reset-password"
            element={<ResetPasswordPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByLabelText("New password"),
    ).toBeInTheDocument();

    expect(
      screen.getByLabelText("Confirm new password"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", {
        name: /set my new password/i,
      }),
    ).toBeInTheDocument();
  });

  it("removes the reset token from the visible browser URL", () => {
    window.history.replaceState(
      {},
      "",
      "/reset-password?token=test-reset-token",
    );

    render(
      <MemoryRouter
        initialEntries={[
          "/reset-password?token=test-reset-token",
        ]}
      >
        <Routes>
          <Route
            path="/reset-password"
            element={<ResetPasswordPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    expect(window.location.search).toBe("");
  });

  it("requires matching passwords before submitting", async () => {
    confirmPasswordResetMock.mockResolvedValue({
      detail:
        "Password reset successful. You can now sign in with your new password.",
    });

    render(
      <MemoryRouter
        initialEntries={[
          "/reset-password?token=test-reset-token",
        ]}
      >
        <Routes>
          <Route
            path="/reset-password"
            element={<ResetPasswordPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    fireEvent.change(
      screen.getByLabelText("New password"),
      {
        target: {
          value: "Secure-Password-2026!",
        },
      },
    );

    fireEvent.change(
      screen.getByLabelText("Confirm new password"),
      {
        target: {
          value: "Different-Password-2026!",
        },
      },
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: /set my new password/i,
      }),
    );

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent(/passwords do not match/i);

    expect(
      confirmPasswordResetMock,
    ).not.toHaveBeenCalled();
  });

  it("submits only the backend reset contract", async () => {
    confirmPasswordResetMock.mockResolvedValue({
      detail:
        "Password reset successful. You can now sign in with your new password.",
    });

    render(
      <MemoryRouter
        initialEntries={[
          "/reset-password?token=test-reset-token",
        ]}
      >
        <Routes>
          <Route
            path="/reset-password"
            element={<ResetPasswordPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    fireEvent.change(
      screen.getByLabelText("New password"),
      {
        target: {
          value: "Secure-Password-2026!",
        },
      },
    );

    fireEvent.change(
      screen.getByLabelText("Confirm new password"),
      {
        target: {
          value: "Secure-Password-2026!",
        },
      },
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: /set my new password/i,
      }),
    );

    await waitFor(() => {
      expect(
        confirmPasswordResetMock,
      ).toHaveBeenCalledWith({
        token: "test-reset-token",
        new_password: "Secure-Password-2026!",
      });
    });

    expect(
      screen.getByRole("heading", {
        name: /password updated/i,
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /your password has been changed/i,
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", {
        name: /continue to sign in/i,
      }),
    ).toHaveAttribute("href", "/login");
  });
});