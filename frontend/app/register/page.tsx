import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  AuthenticationApiError,
  register,
} from "../../src/auth/authApi";

export default function RegisterPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [registered, setRegistered] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalizedEmail = email.trim();
    const normalizedUsername = username.trim();

    if (password !== passwordConfirmation) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await register({
        email: normalizedEmail,
        username: normalizedUsername,
        password,
      });

      /*
       * Registration deliberately does not establish an authenticated
       * session. The account must complete email verification first.
       */
      setRegistered(true);
      setPassword("");
      setPasswordConfirmation("");
    } catch (cause) {
      setError(
        cause instanceof AuthenticationApiError
          ? cause.message
          : "Unable to create the account. Please try again later.",
      );
    } finally {
      setLoading(false);
    }
  }

  if (registered) {
    return (
      <main
        aria-label="Email verification required"
        style={styles.page}
      >
        <section style={styles.card} aria-labelledby="registration-success">
          <div style={styles.eyebrow}>EASYCHATBOT ACADEMY</div>
          <h1 id="registration-success" style={styles.title}>
            Check your email
          </h1>
          <p style={styles.text}>
            Your account has been created. We sent a verification link to{" "}
            <strong>{email.trim()}</strong>.
          </p>
          <p style={styles.muted}>
            Your account remains unverified until you use that link. You can
            then sign in normally.
          </p>

          <div style={styles.actions}>
            <button
              type="button"
              onClick={() => navigate("/login", { replace: true })}
              style={styles.primaryButton}
            >
              Go to sign in
            </button>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main style={styles.page}>
      <section style={styles.card} aria-labelledby="register-title">
        <div style={styles.eyebrow}>EASYCHATBOT ACADEMY</div>
        <h1 id="register-title" style={styles.title}>
          Create your account
        </h1>
        <p style={styles.text}>
          Register for authorized Academy access. Email verification is
          required before you can sign in.
        </p>

        <form onSubmit={handleSubmit} noValidate>
          <div style={styles.field}>
            <label htmlFor="register-email">Email</label>
            <input
              id="register-email"
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>

          <div style={styles.field}>
            <label htmlFor="register-username">Username</label>
            <input
              id="register-username"
              name="username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </div>

          <div style={styles.field}>
            <label htmlFor="register-password">Password</label>
            <input
              id="register-password"
              name="password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>

          <div style={styles.field}>
            <label htmlFor="register-password-confirmation">
              Confirm password
            </label>
            <input
              id="register-password-confirmation"
              name="passwordConfirmation"
              type="password"
              autoComplete="new-password"
              value={passwordConfirmation}
              onChange={(event) =>
                setPasswordConfirmation(event.target.value)
              }
              required
            />
          </div>

          {error ? (
            <p role="alert" style={styles.error}>
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={loading}
            style={styles.primaryButton}
          >
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p style={styles.footerText}>
          Already registered?{" "}
          <Link to="/login">Sign in</Link>
        </p>
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
    maxWidth: "460px",
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
  muted: {
    lineHeight: 1.55,
    opacity: 0.72,
  },
  field: {
    display: "grid",
    gap: "0.4rem",
    marginBottom: "1rem",
  },
  actions: {
    marginTop: "1.5rem",
  },
  primaryButton: {
    width: "100%",
    minHeight: "44px",
    border: 0,
    borderRadius: "10px",
    padding: "0.7rem 1rem",
    cursor: "pointer",
    fontWeight: 700,
  },
  error: {
    color: "#a32929",
    marginBottom: "1rem",
  },
  footerText: {
    marginTop: "1.25rem",
    textAlign: "center" as const,
    opacity: 0.8,
  },
};
