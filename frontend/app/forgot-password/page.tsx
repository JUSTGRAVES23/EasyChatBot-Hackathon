"use client";

import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import {
  AuthenticationApiError,
  requestPasswordReset,
} from "@/src/auth/authApi";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalizedEmail = email.trim();

    if (!normalizedEmail) {
      setError("Please enter your email address.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      await requestPasswordReset({
        email: normalizedEmail,
      });

      /*
       * Security requirement:
       * Never reveal whether the supplied email belongs to an account.
       */
      setSubmitted(true);
    } catch (err) {
      if (err instanceof AuthenticationApiError) {
        setError(err.message);
      } else {
        setError(
          "We couldn't process that request right now. Please try again.",
        );
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        width: "100%",
        display: "flex",
        justifyContent: "center",
        alignItems: "flex-start",
        padding: "18px 16px 48px",
        boxSizing: "border-box",
        background:
          "linear-gradient(180deg, #edf4ff 0%, #f5f9ff 55%, #eef5ff 100%)",
      }}
    >
      <section
        aria-label="Reset your EasyChatBot password"
        style={{
          width: "min(700px, 94vw)",
          margin: 0,
        }}
      >
        {/* =========================================================
            ARTWORK + REAL HTML INTERACTION LAYER
            ========================================================= */}
        <div
          style={{
            position: "relative",
            width: "100%",
            lineHeight: 0,
          }}
        >
          <img
            src="/assets/auth/password-reset-request-design.png"
            alt="EasyChatBot password reset request"
            style={{
              display: "block",
              width: "100%",
              height: "auto",
              border: 0,
              userSelect: "none",
              WebkitUserSelect: "none",
            }}
          />

          {!submitted && (
            <form
              onSubmit={handleSubmit}
              noValidate
              style={{
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                pointerEvents: "none",
              }}
            >
              {/* =====================================================
                  REAL EMAIL INPUT

                  The artwork already contains the visual label
                  "Your email address".

                  Therefore the HTML input sits BELOW the printed
                  label in the blank writing area.
                  ===================================================== */}
              <input
                id="forgot-password-email"
                name="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                aria-label="Your email address"
                autoComplete="email"
                inputMode="email"
                spellCheck={false}
                placeholder=""
                disabled={loading}
                style={{
                  position: "absolute",

                  /*
                   * Carefully positioned inside the blank area
                   * of the artwork's email field.
                   */
                  left: "29.2%",
                  width: "59.8%",
                  top: "53.25%",
                  height: "2.35%",

                  boxSizing: "border-box",
                  margin: 0,
                  padding: "0 0.25rem",

                  border: "0",
                  outline: "none",
                  background: "transparent",
                  boxShadow: "none",

                  color: "#17366f",
                  fontFamily: "inherit",
                  fontSize: "clamp(0.75rem, 1.45vw, 0.95rem)",
                  fontWeight: 500,
                  lineHeight: 1.2,

                  appearance: "none",
                  WebkitAppearance: "none",

                  pointerEvents: "auto",
                  opacity: loading ? 0.65 : 1,
                }}
              />

              {/* =====================================================
                  REAL SUBMIT BUTTON

                  The artwork supplies the visual button.
                  This transparent button supplies the actual
                  HTML interaction and form submission.
                  ===================================================== */}
              <button
                type="submit"
                disabled={loading}
                aria-label={
                  loading
                    ? "Sending password reset link"
                    : "Send me a reset link"
                }
                style={{
                  position: "absolute",

                  left: "19.8%",
                  width: "70.2%",
                  top: "56.05%",
                  height: "4.45%",

                  padding: 0,
                  margin: 0,

                  border: 0,
                  borderRadius: 0,

                  background: "transparent",
                  color: "transparent",

                  fontSize: 0,
                  lineHeight: 0,

                  cursor: loading ? "wait" : "pointer",

                  pointerEvents: "auto",

                  appearance: "none",
                  WebkitAppearance: "none",
                }}
              >
                <span
                  style={{
                    position: "absolute",
                    width: "1px",
                    height: "1px",
                    padding: 0,
                    margin: "-1px",
                    overflow: "hidden",
                    clip: "rect(0, 0, 0, 0)",
                    whiteSpace: "nowrap",
                    border: 0,
                  }}
                >
                  {loading
                    ? "Sending password reset link"
                    : "Send me a reset link"}
                </span>
              </button>
            </form>
          )}
        </div>

        {/* =========================================================
            ERROR STATE

            Deliberately outside the artwork so an error never
            obscures the visual design or CTA.
            ========================================================= */}
        {error && !submitted && (
          <div
            role="alert"
            style={{
              width: "min(620px, 92%)",
              margin: "12px auto 0",

              boxSizing: "border-box",

              padding: "10px 14px",

              background: "rgba(255, 247, 247, 0.98)",
              border: "1px solid rgba(166, 27, 27, 0.14)",
              borderRadius: "10px",

              color: "#9b2424",

              fontFamily: "inherit",
              fontSize: "clamp(0.7rem, 1.3vw, 0.82rem)",
              fontWeight: 600,
              lineHeight: 1.35,

              textAlign: "center",

              boxShadow: "0 4px 14px rgba(23, 54, 111, 0.05)",
            }}
          >
            {error}
          </div>
        )}

        {/* =========================================================
            SUCCESS STATE

            IMPORTANT:
            This is intentionally OUTSIDE the artwork.

            The artwork remains completely untouched and visible.
            The confirmation gently appears underneath it.
            ========================================================= */}
        {submitted && (
          <>
            <style>
              {`
                @keyframes easyChatBotResetSuccessIn {
                  from {
                    opacity: 0;
                    transform: translateY(-7px);
                  }

                  to {
                    opacity: 1;
                    transform: translateY(0);
                  }
                }
              `}
            </style>

            <div
              role="status"
              aria-live="polite"
              style={{
                width: "min(620px, 92%)",
                margin: "14px auto 0",

                boxSizing: "border-box",

                display: "flex",
                alignItems: "center",
                gap: "12px",

                padding: "12px 16px",

                background:
                  "linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(244,249,255,0.99) 100%)",

                border: "1px solid rgba(23, 54, 111, 0.10)",
                borderRadius: "12px",

                boxShadow: "0 6px 20px rgba(23, 54, 111, 0.08)",

                color: "#17366f",

                fontFamily: "inherit",
                lineHeight: 1.35,

                animation:
                  "easyChatBotResetSuccessIn 240ms cubic-bezier(0.22, 1, 0.36, 1)",
              }}
            >
              {/* Success icon */}
              <div
                aria-hidden="true"
                style={{
                  flex: "0 0 auto",

                  width: "34px",
                  height: "34px",

                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",

                  borderRadius: "50%",

                  background: "#e8f6ef",
                  color: "#16834b",

                  fontSize: "18px",
                  fontWeight: 700,
                  lineHeight: 1,
                }}
              >
                ✓
              </div>

              {/* Success copy */}
              <div
                style={{
                  minWidth: 0,
                  textAlign: "left",
                }}
              >
                <div
                  style={{
                    marginBottom: "2px",

                    fontSize: "clamp(0.82rem, 1.5vw, 0.95rem)",
                    fontWeight: 700,

                    color: "#17366f",
                  }}
                >
                  Check your inbox
                </div>

                <div
                  style={{
                    fontSize: "clamp(0.68rem, 1.25vw, 0.8rem)",
                    fontWeight: 500,

                    color: "#47618f",
                  }}
                >
                  If an EasyChatBot account exists for that email, we've sent
                  instructions to reset your password.
                </div>
              </div>
            </div>
          </>
        )}

        {/* =========================================================
            BACK TO LOGIN
            ========================================================= */}
        <div
          style={{
            width: "100%",

            display: "flex",
            justifyContent: "center",

            paddingTop: submitted ? "12px" : "14px",

            lineHeight: 1.4,
          }}
        >
          <Link
            to="/login"
            style={{
              color: "#17366f",

              fontSize: "0.9rem",
              fontWeight: 600,

              textDecoration: "none",
            }}
          >
            ← Back to sign in
          </Link>
        </div>
      </section>
    </main>
  );
}