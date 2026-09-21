"use client";

import {
  FormEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import {
  AuthenticationApiError,
  confirmPasswordReset,
  getPasswordResetContext,
} from "../../src/auth/authApi";

type ScreenState =
  | "create"
  | "validating"
  | "success"
  | "invalid";

type PasswordChecks = {
  length: boolean;
  uppercase: boolean;
  lowercase: boolean;
  number: boolean;
  special: boolean;
};

function evaluatePassword(password: string): PasswordChecks {
  return {
    length: password.length >= 12,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };
}

function CheckItem({
  checked,
  children,
}: {
  checked: boolean;
  children: ReactNode;
}) {
  return (
    <li
      style={{
        display: "flex",
        alignItems: "center",
        gap: "9px",
        color: checked ? "#16834b" : "#65779b",
        fontWeight: checked ? 650 : 500,
        fontSize: "0.84rem",
        lineHeight: 1.35,
        transition: "color 160ms ease",
      }}
    >
      <span
        aria-hidden="true"
        style={{
          width: "19px",
          height: "19px",
          flex: "0 0 19px",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: "50%",
          border: checked
            ? "1px solid #16834b"
            : "1px solid #c8d3e4",
          background: checked ? "#e8f6ef" : "#ffffff",
          color: checked ? "#16834b" : "transparent",
          fontSize: "12px",
          fontWeight: 800,
          transition:
            "background 160ms ease, border-color 160ms ease",
        }}
      >
        ✓
      </span>
      {children}
    </li>
  );
}

function PasswordField({
  id,
  label,
  value,
  visible,
  onChange,
  onToggle,
  disabled,
}: {
  id: string;
  label: string;
  value: string;
  visible: boolean;
  onChange: (value: string) => void;
  onToggle: () => void;
  disabled: boolean;
}) {
  return (
    <div style={{ marginBottom: "16px" }}>
      <label
        htmlFor={id}
        style={{
          display: "block",
          marginBottom: "7px",
          color: "#17366f",
          fontSize: "0.88rem",
          fontWeight: 700,
        }}
      >
        {label}
      </label>

      <div
        style={{
          position: "relative",
        }}
      >
        <input
          id={id}
          name={id}
          type={visible ? "text" : "password"}
          autoComplete="new-password"
          minLength={12}
          maxLength={256}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          disabled={disabled}
          required
          style={{
            width: "100%",
            minHeight: "50px",
            padding: "0 48px 0 15px",
            boxSizing: "border-box",
            border: "1px solid #cbd7e8",
            borderRadius: "11px",
            background: "#ffffff",
            color: "#17366f",
            fontSize: "0.96rem",
            outline: "none",
            boxShadow: "0 1px 2px rgba(23, 54, 111, 0.03)",
          }}
        />

        <button
          type="button"
          onClick={onToggle}
          disabled={disabled}
          aria-label={visible ? `Hide ${label}` : `Show ${label}`}
          style={{
            position: "absolute",
            top: "50%",
            right: "9px",
            transform: "translateY(-50%)",
            width: "34px",
            height: "34px",
            padding: 0,
            border: 0,
            borderRadius: "8px",
            background: "transparent",
            color: "#55709e",
            cursor: disabled ? "not-allowed" : "pointer",
            fontSize: "17px",
          }}
        >
          {visible ? "◉" : "◌"}
        </button>
      </div>
    </div>
  );
}

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const [token, setToken] = useState("");
  const [email, setEmail] = useState("");
  const [screenState, setScreenState] =
    useState<ScreenState>("create");
  const [contextLoading, setContextLoading] = useState(true);

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [newPasswordVisible, setNewPasswordVisible] =
    useState(false);
  const [confirmPasswordVisible, setConfirmPasswordVisible] =
    useState(false);

  const [error, setError] = useState<string | null>(null);
  const initialized = useRef(false);

  const checks = useMemo(
    () => evaluatePassword(newPassword),
    [newPassword],
  );

  const passedChecks = Object.values(checks).filter(Boolean).length;
  const strengthPercent = Math.round(
    (passedChecks / 5) * 100,
  );

  const passwordsMatch =
    confirmPassword.length > 0 &&
    newPassword === confirmPassword;

  useEffect(() => {
    if (initialized.current) {
      return;
    }

    initialized.current = true;

    const rawToken = searchParams.get("token")?.trim() ?? "";

    if (!rawToken) {
      setContextLoading(false);
      setScreenState("invalid");
      setError(
        "This password reset link is missing or invalid.",
      );
      return;
    }

    setToken(rawToken);

    let cancelled = false;

    async function loadContext() {
      try {
        const context = await getPasswordResetContext(
          rawToken,
        );

        if (cancelled) {
          return;
        }

        setEmail(context.email);
        setContextLoading(false);
        setScreenState("create");

        // Only remove the bearer token after the backend has confirmed it.
        // The token remains in component state for the actual reset.
        window.history.replaceState(
          {},
          document.title,
          window.location.pathname,
        );
      } catch (cause) {
        if (cancelled) {
          return;
        }

        setContextLoading(false);
        setScreenState("invalid");
        setError(
          cause instanceof AuthenticationApiError
            ? cause.message
            : "This password reset link is invalid or has expired.",
        );
      }
    }

    void loadContext();

    return () => {
      cancelled = true;
    };
  }, [searchParams]);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError(null);

    if (!token) {
      setScreenState("invalid");
      setError(
        "This password reset link is missing or invalid.",
      );
      return;
    }

    if (passedChecks !== 5) {
      setError(
        "Please meet all password requirements before continuing.",
      );
      return;
    }

    if (!passwordsMatch) {
      setError("Passwords do not match.");
      return;
    }

    setScreenState("validating");

    try {
      await confirmPasswordReset({
        token,
        new_password: newPassword,
      });

      /*
       * Clear all sensitive material from component state after
       * the backend has atomically completed the reset.
       */
      setToken("");
      setNewPassword("");
      setConfirmPassword("");
      setNewPasswordVisible(false);
      setConfirmPasswordVisible(false);
      setScreenState("success");
    } catch (cause) {
      setScreenState("create");
      setError(
        cause instanceof AuthenticationApiError
          ? cause.message
          : "We couldn't update your password. Please try again.",
      );
    }
  }

  if (contextLoading) {
    return (
      <main
        aria-label="Validating password reset link"
        style={styles.page}
      >
        <section style={styles.card}>
          <div style={styles.logoMark}>E</div>
          <div style={styles.eyebrow}>EASYCHATBOT ACCOUNT SECURITY</div>
          <h1 style={styles.title}>Validating your reset link</h1>
          <p style={styles.text}>
            Just a moment — we're securely checking your
            password reset request.
          </p>
          <div
            role="status"
            aria-live="polite"
            style={styles.loadingBar}
          >
            <span style={styles.loadingBarFill} />
          </div>
        </section>
      </main>
    );
  }

  if (screenState === "invalid") {
    return (
      <main
        aria-label="Password reset link invalid"
        style={styles.page}
      >
        <section style={styles.card}>
          <div style={styles.logoMark}>E</div>
          <div style={styles.eyebrow}>EASYCHATBOT ACCOUNT SECURITY</div>
          <h1 style={styles.title}>Reset link unavailable</h1>
          <p role="alert" style={styles.text}>
            {error ??
              "This password reset link is invalid or has expired."}
          </p>
          <Link
            href="/forgot-password"
            style={styles.primaryLink}
          >
            Request a new link →
          </Link>
        </section>
      </main>
    );
  }

  if (screenState === "success") {
    return (
      <main
        aria-label="Password reset successful"
        style={styles.page}
      >
        <section style={styles.card}>
          <div style={styles.successIcon} aria-hidden="true">
            ✓
          </div>

          <div style={styles.eyebrow}>EASYCHATBOT ACCOUNT SECURITY</div>

          <h1 style={styles.title}>All set!</h1>

          <p style={styles.text}>
            Your EasyChatBot account password has been updated
            successfully.
          </p>

          <div style={styles.securityNote}>
            <strong>Signed out everywhere else.</strong>
            <br />
            For your safety, we've signed you out from any
            other devices. You can now sign in with your new
            password.
          </div>

          <Link
            href="/login"
            style={styles.primaryLink}
          >
            Go to sign in →
          </Link>

          <Link
            href="/welcome"
            style={styles.secondaryLink}
          >
            Explore EasyChatBot and keep learning →
          </Link>
        </section>
      </main>
    );
  }

  const validating = screenState === "validating";

  return (
    <main
      aria-label="Create new EasyChatBot password"
      style={styles.page}
    >
      <section style={styles.card}>
        <div style={styles.logoMark}>E</div>
        <div style={styles.eyebrow}>EASYCHATBOT ACCOUNT SECURITY</div>

        <h1 style={styles.title}>
          Let&apos;s get you back in 🔐
        </h1>

        <p style={styles.text}>
          Create a new password for your EasyChatBot account.
        </p>

        <div style={styles.accountLine}>
          <span>Resetting the password for</span>
          <strong>{email} ✓</strong>
        </div>

        <form onSubmit={handleSubmit}>
          <PasswordField
            id="new-password"
            label="New password"
            value={newPassword}
            visible={newPasswordVisible}
            onChange={setNewPassword}
            onToggle={() =>
              setNewPasswordVisible(
                (visible) => !visible,
              )
            }
            disabled={validating}
          />

          <PasswordField
            id="confirm-password"
            label="Confirm new password"
            value={confirmPassword}
            visible={confirmPasswordVisible}
            onChange={setConfirmPassword}
            onToggle={() =>
              setConfirmPasswordVisible(
                (visible) => !visible,
              )
            }
            disabled={validating}
          />

          <div style={styles.strengthHeader}>
            <span>Password strength</span>
            <strong>
              {strengthPercent === 100
                ? "Strong"
                : strengthPercent >= 60
                  ? "Getting there"
                  : "Needs work"}
            </strong>
          </div>

          <div
            aria-label={`Password strength ${strengthPercent}%`}
            style={styles.progressTrack}
          >
            <div
              style={{
                ...styles.progressFill,
                width: `${strengthPercent}%`,
              }}
            />
          </div>

          <ul
            aria-label="Password requirements"
            style={styles.requirements}
          >
            <CheckItem checked={checks.length}>
              At least 12 characters
            </CheckItem>
            <CheckItem checked={checks.uppercase}>
              At least one uppercase letter
            </CheckItem>
            <CheckItem checked={checks.lowercase}>
              At least one lowercase letter
            </CheckItem>
            <CheckItem checked={checks.number}>
              At least one number
            </CheckItem>
            <CheckItem checked={checks.special}>
              At least one special character
            </CheckItem>
            <CheckItem checked={false}>
              Different from your previous password
            </CheckItem>
          </ul>

          <p style={styles.previousPasswordNote}>
            The previous-password check is performed securely
            by EasyChatBot when you submit.
          </p>

          {passwordsMatch && (
            <p
              role="status"
              style={styles.matchSuccess}
            >
              ✓ Passwords match
            </p>
          )}

          {error && (
            <p
              role="alert"
              style={styles.error}
            >
              {error}
            </p>
          )}

          {validating && (
            <p
              role="status"
              aria-live="polite"
              style={styles.validatingText}
            >
              Validating your password and securing your
              account…
            </p>
          )}

          <button
            type="submit"
            disabled={
              validating ||
              !token ||
              passedChecks !== 5 ||
              !passwordsMatch
            }
            style={{
              ...styles.button,
              opacity:
                validating ||
                !token ||
                passedChecks !== 5 ||
                !passwordsMatch
                  ? 0.55
                  : 1,
              cursor:
                validating ||
                !token ||
                passedChecks !== 5 ||
                !passwordsMatch
                  ? "not-allowed"
                  : "pointer",
            }}
          >
            {validating
              ? "Validating…"
              : "Set my new password →"}
          </button>
        </form>

        <Link
          href="/login"
          style={styles.secondaryLink}
        >
          ← Back to sign in
        </Link>
      </section>
    </main>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "flex-start",
    padding: "32px 16px 56px",
    boxSizing: "border-box" as const,
    background:
      "linear-gradient(180deg, #edf4ff 0%, #f8fbff 55%, #eef5ff 100%)",
    color: "#17366f",
    fontFamily:
      "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },

  card: {
    width: "min(560px, 100%)",
    padding: "32px",
    boxSizing: "border-box" as const,
    border: "1px solid rgba(23, 54, 111, 0.10)",
    borderRadius: "24px",
    background:
      "linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(248,251,255,0.99) 100%)",
    boxShadow:
      "0 24px 70px rgba(23, 54, 111, 0.13)",
  },

  logoMark: {
    width: "42px",
    height: "42px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: "18px",
    borderRadius: "12px",
    background: "#17366f",
    color: "#ffffff",
    fontSize: "22px",
    fontWeight: 800,
  },

  eyebrow: {
    marginBottom: "9px",
    color: "#6681ac",
    fontSize: "0.72rem",
    fontWeight: 800,
    letterSpacing: "0.13em",
  },

  title: {
    margin: "0 0 10px",
    color: "#17366f",
    fontSize: "clamp(1.65rem, 4vw, 2.15rem)",
    lineHeight: 1.16,
    letterSpacing: "-0.025em",
  },

  text: {
    margin: "0 0 20px",
    color: "#536b91",
    fontSize: "0.96rem",
    lineHeight: 1.6,
  },

  accountLine: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: "4px 7px",
    marginBottom: "22px",
    padding: "12px 14px",
    border: "1px solid rgba(23, 54, 111, 0.08)",
    borderRadius: "11px",
    background: "#f2f6fd",
    color: "#60769a",
    fontSize: "0.82rem",
    lineHeight: 1.4,
  },

  strengthHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "2px",
    marginBottom: "7px",
    color: "#60769a",
    fontSize: "0.78rem",
    fontWeight: 650,
  },

  progressTrack: {
    width: "100%",
    height: "7px",
    marginBottom: "17px",
    overflow: "hidden",
    borderRadius: "999px",
    background: "#e5ebf4",
  },

  progressFill: {
    height: "100%",
    borderRadius: "999px",
    background: "#16834b",
    transition: "width 180ms ease",
  },

  requirements: {
    display: "grid",
    gap: "9px",
    margin: "0 0 7px",
    padding: 0,
    listStyle: "none",
  },

  previousPasswordNote: {
    margin: "7px 0 17px",
    color: "#7586a2",
    fontSize: "0.75rem",
    lineHeight: 1.45,
  },

  matchSuccess: {
    margin: "0 0 12px",
    color: "#16834b",
    fontSize: "0.82rem",
    fontWeight: 650,
  },

  error: {
    margin: "0 0 14px",
    padding: "10px 12px",
    border: "1px solid rgba(166, 27, 27, 0.13)",
    borderRadius: "10px",
    background: "#fff7f7",
    color: "#9b2424",
    fontSize: "0.82rem",
    lineHeight: 1.45,
  },

  validatingText: {
    margin: "0 0 14px",
    color: "#55709e",
    fontSize: "0.82rem",
    fontWeight: 650,
    lineHeight: 1.45,
  },

  button: {
    width: "100%",
    minHeight: "51px",
    marginTop: "4px",
    border: 0,
    borderRadius: "11px",
    background: "#17366f",
    color: "#ffffff",
    fontSize: "0.92rem",
    fontWeight: 750,
    boxShadow:
      "0 8px 18px rgba(23, 54, 111, 0.16)",
    transition: "opacity 160ms ease",
  },

  secondaryLink: {
    display: "block",
    marginTop: "18px",
    color: "#55709e",
    fontSize: "0.83rem",
    fontWeight: 650,
    textAlign: "center" as const,
    textDecoration: "none",
  },

  primaryLink: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    width: "100%",
    minHeight: "50px",
    boxSizing: "border-box" as const,
    borderRadius: "11px",
    background: "#17366f",
    color: "#ffffff",
    fontSize: "0.92rem",
    fontWeight: 750,
    textDecoration: "none",
    boxShadow:
      "0 8px 18px rgba(23, 54, 111, 0.16)",
  },

  successIcon: {
    width: "62px",
    height: "62px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: "18px",
    borderRadius: "50%",
    background: "#e8f6ef",
    color: "#16834b",
    fontSize: "32px",
    fontWeight: 800,
  },

  securityNote: {
    margin: "18px 0 22px",
    padding: "15px 16px",
    border: "1px solid rgba(22, 131, 75, 0.12)",
    borderRadius: "12px",
    background: "#f0faf5",
    color: "#356b50",
    fontSize: "0.82rem",
    lineHeight: 1.55,
  },

  loadingBar: {
    width: "100%",
    height: "7px",
    overflow: "hidden",
    borderRadius: "999px",
    background: "#e5ebf4",
  },

  loadingBarFill: {
    display: "block",
    width: "42%",
    height: "100%",
    borderRadius: "999px",
    background: "#17366f",
  },
};


export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <main aria-label="Validating password reset link" style={styles.page}>
          <section style={styles.card}>
            <div style={styles.logoMark}>E</div>
            <div style={styles.eyebrow}>EASYCHATBOT ACCOUNT SECURITY</div>
            <h1 style={styles.title}>Validating your reset link</h1>
            <p style={styles.text}>
              Just a moment — we&apos;re securely checking your password reset request.
            </p>
            <div role="status" aria-live="polite" style={styles.loadingBar}>
              <span style={styles.loadingBarFill} />
            </div>
          </section>
        </main>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  );
}
