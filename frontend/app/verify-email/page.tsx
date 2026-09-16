import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import {
  AuthenticationApiError,
  verifyEmail,
} from "../../src/auth/authApi";

type VerificationState =
  | "checking"
  | "verified"
  | "failed"
  | "missing";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const [state, setState] = useState<VerificationState>("checking");
  const [error, setError] = useState<string | null>(null);
  const verificationStarted = useRef(false);

  useEffect(() => {
    if (verificationStarted.current) {
      return;
    }

    verificationStarted.current = true;

    const token = searchParams.get("token")?.trim() ?? "";

    /*
     * Remove the raw verification token from the visible URL as soon as it
     * has been captured. The token is still submitted to the backend, but
     * it is never rendered, logged, or stored in application state.
     */
    if (token) {
      const cleanUrl = `${window.location.pathname}${window.location.hash}`;
      window.history.replaceState({}, document.title, cleanUrl);
    }

    if (!token) {
      setState("missing");
      return;
    }

    void verifyEmail(token)
      .then(() => {
        setState("verified");
      })
      .catch((cause) => {
        setState("failed");
        setError(
          cause instanceof AuthenticationApiError
            ? cause.message
            : "This verification link is invalid or has expired.",
        );
      });
  }, [searchParams]);

  if (state === "checking") {
    return (
      <main style={styles.page} aria-label="Email verification">
        <section style={styles.card} aria-live="polite">
          <div style={styles.eyebrow}>EASYCHATBOT ACADEMY</div>
          <h1 style={styles.title}>Verifying your email…</h1>
          <p style={styles.text}>
            Please wait while we confirm your verification link.
          </p>
        </section>
      </main>
    );
  }

  if (state === "verified") {
    return (
      <main style={styles.page} aria-label="Email verified">
        <section style={styles.card} aria-labelledby="verified-title">
          <div style={styles.eyebrow}>EASYCHATBOT ACADEMY</div>
          <h1 id="verified-title" style={styles.title}>
            Email verified
          </h1>
          <p style={styles.text}>
            Your account is now verified. You can sign in and continue to the
            Academy.
          </p>
          <Link to="/login" style={styles.primaryLink}>
            Continue to sign in
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main style={styles.page} aria-label="Email verification failed">
      <section style={styles.card} aria-labelledby="verification-error-title">
        <div style={styles.eyebrow}>EASYCHATBOT ACADEMY</div>
        <h1 id="verification-error-title" style={styles.title}>
          Verification could not be completed
        </h1>
        <p role="alert" style={styles.error}>
          {error ??
            "No verification token was provided. Please use the link from your registration email."}
        </p>
        <p style={styles.text}>
          If the link has expired or has already been used, return to sign in.
          Resending verification emails will be implemented as the next AVW-01
          slice.
        </p>
        <Link to="/login" style={styles.primaryLink}>
          Return to sign in
        </Link>
      </section>
    </main>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "grid",
    placeItems: "center",
    padding: "2rem",
    boxSizing: "border-box" as const,
  },
  card: {
    width: "100%",
    maxWidth: "560px",
    padding: "2rem",
    border: "1px solid rgba(70, 55, 95, 0.18)",
    borderRadius: "20px",
    background: "rgba(255, 255, 255, 0.96)",
    boxShadow: "0 18px 50px rgba(50, 35, 75, 0.12)",
    boxSizing: "border-box" as const,
  },
  eyebrow: {
    fontSize: "0.75rem",
    fontWeight: 700,
    letterSpacing: "0.12em",
    opacity: 0.7,
    marginBottom: "0.75rem",
  },
  title: {
    margin: "0 0 0.75rem",
  },
  text: {
    lineHeight: 1.55,
  },
  error: {
    color: "#a32929",
    lineHeight: 1.55,
  },
  primaryLink: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "44px",
    padding: "0.7rem 1rem",
    borderRadius: "10px",
    textDecoration: "none",
    fontWeight: 700,
  },
};
