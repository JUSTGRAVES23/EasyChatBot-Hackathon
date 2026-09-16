import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import RegisterPage from "../../app/register/page";
import VerifyEmailPage from "../../app/verify-email/page";

/*
 * Vitest hoists vi.mock() calls. Any mock values referenced by the
 * mock factory therefore need to be created with vi.hoisted().
 */
const {
  registerMock,
  verifyEmailMock,
} = vi.hoisted(() => ({
  registerMock: vi.fn(),
  verifyEmailMock: vi.fn(),
}));

vi.mock("../../src/auth/authApi", () => ({
  AuthenticationApiError: class AuthenticationApiError extends Error {
    readonly status: number;

    constructor(message: string, status: number) {
      super(message);
      this.name = "AuthenticationApiError";
      this.status = status;
    }
  },

  register: registerMock,
  verifyEmail: verifyEmailMock,
}));

describe("AVW-01 registration and verification pages", () => {
  beforeEach(() => {
    registerMock.mockReset();
    verifyEmailMock.mockReset();

    window.history.replaceState({}, "", "/");
  });

  it("registers an account and moves to the check-email state", async () => {
    registerMock.mockResolvedValue({
      detail: "Registration successful.",
    });

    render(
      <MemoryRouter initialEntries={["/register"]}>
        <RegisterPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText("Email"), {
      target: {
        value: "new@example.com",
      },
    });

    fireEvent.change(screen.getByLabelText("Username"), {
      target: {
        value: "newuser",
      },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: {
        value: "StrongPassword123!",
      },
    });

    fireEvent.change(screen.getByLabelText("Confirm password"), {
      target: {
        value: "StrongPassword123!",
      },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Create account",
      }),
    );

    await waitFor(() => {
      expect(registerMock).toHaveBeenCalledWith({
        email: "new@example.com",
        username: "newuser",
        password: "StrongPassword123!",
      });
    });

    expect(
      await screen.findByRole("heading", {
        name: "Check your email",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(/new@example\.com/),
    ).toBeInTheDocument();
  });

  it("does not call registration when passwords differ", () => {
    render(
      <MemoryRouter initialEntries={["/register"]}>
        <RegisterPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText("Email"), {
      target: {
        value: "new@example.com",
      },
    });

    fireEvent.change(screen.getByLabelText("Username"), {
      target: {
        value: "newuser",
      },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: {
        value: "one",
      },
    });

    fireEvent.change(screen.getByLabelText("Confirm password"), {
      target: {
        value: "two",
      },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Create account",
      }),
    );

    expect(registerMock).not.toHaveBeenCalled();

    expect(
      screen.getByRole("alert"),
    ).toHaveTextContent(
      "Passwords do not match.",
    );
  });

  it("verifies a token and never renders the raw token", async () => {
    verifyEmailMock.mockResolvedValue({
      detail: "Email verified.",
    });

    const token = "sensitive-test-token";

    render(
      <MemoryRouter
        initialEntries={[
          `/verify-email?token=${encodeURIComponent(token)}`,
        ]}
      >
        <VerifyEmailPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(verifyEmailMock).toHaveBeenCalledWith(token);
    });

    expect(
      await screen.findByRole("heading", {
        name: "Email verified",
      }),
    ).toBeInTheDocument();

    /*
     * Security requirement:
     * the raw verification token must never be rendered.
     */
    expect(
      screen.queryByText(token),
    ).not.toBeInTheDocument();

    /*
     * The verification page should remove the token from the
     * visible browser URL after consuming it.
     */
    expect(window.location.search).toBe("");
  });

  it("fails safely when no verification token is supplied", async () => {
    render(
      <MemoryRouter initialEntries={["/verify-email"]}>
        <VerifyEmailPage />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", {
        name: "Verification could not be completed",
      }),
    ).toBeInTheDocument();

    expect(
      verifyEmailMock,
    ).not.toHaveBeenCalled();
  });
});