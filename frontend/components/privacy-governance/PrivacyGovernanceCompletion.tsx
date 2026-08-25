"use client";

import React from "react";

export type PrivacyGovernanceTerminalStatus =
  | "APPROVED"
  | "COMPLETED"
  | "BLOCKED"
  | "REJECTED";

interface PrivacyGovernanceCompletionProps {
  caseId: string;
  changeId: string;
  status: PrivacyGovernanceTerminalStatus;
  title?: string;
  summary?: string;
  onReturnToCases?: () => void;
}

function getStatusLabel(
  status: PrivacyGovernanceTerminalStatus,
): string {
  switch (status) {
    case "APPROVED":
    case "COMPLETED":
      return "COMPLETED";

    case "BLOCKED":
      return "BLOCKED";

    case "REJECTED":
      return "REJECTED";

    default:
      return status;
  }
}

function getHeadline(
  status: PrivacyGovernanceTerminalStatus,
): string {
  switch (status) {
    case "APPROVED":
    case "COMPLETED":
      return "Congratulations!";

    case "BLOCKED":
    case "REJECTED":
      return "Assessment completed";

    default:
      return "Assessment completed";
  }
}

function getMessage(
  status: PrivacyGovernanceTerminalStatus,
): string {
  switch (status) {
    case "APPROVED":
    case "COMPLETED":
      return (
        "The privacy governance assessment has been completed successfully. " +
        "No further action is required."
      );

    case "BLOCKED":
      return (
        "The privacy governance assessment has been completed and the case " +
        "has been blocked. No further action is required."
      );

    case "REJECTED":
      return (
        "The privacy governance assessment has been completed and the case " +
        "has been rejected. No further action is required."
      );

    default:
      return "This privacy governance assessment has been completed.";
  }
}

export default function PrivacyGovernanceCompletion({
  caseId,
  changeId,
  status,
  title,
  summary,
  onReturnToCases,
}: PrivacyGovernanceCompletionProps) {
  const statusLabel = getStatusLabel(status);
  const headline = getHeadline(status);
  const message = getMessage(status);

  return (
    <main className="privacy-completion-page">
      <section
        className="privacy-completion-card"
        aria-labelledby="privacy-completion-title"
      >
        <div className="privacy-completion-hero">
          <div
            className="privacy-completion-confetti"
            aria-hidden="true"
          >
            <span>✦</span>
            <span>◆</span>
            <span>✦</span>
            <span>•</span>
            <span>◆</span>
          </div>

          <img
            src="/images/easychatbot-mascot.png"
            alt="EasyChatBot"
            className="privacy-completion-mascot"
          />

          <div
            className={`privacy-completion-status-icon ${
              statusLabel === "COMPLETED"
                ? "success"
                : "terminal"
            }`}
            aria-hidden="true"
          >
            ✓
          </div>

          <h1 id="privacy-completion-title">
            {headline}
          </h1>

          <h2>Case completed</h2>

          <p className="privacy-completion-message">
            {message}
          </p>
        </div>

        <div className="privacy-completion-details">
          {title && (
            <div className="privacy-completion-detail-row">
              <div className="privacy-detail-label">
                <span
                  className="privacy-detail-icon blue"
                  aria-hidden="true"
                >
                  □
                </span>

                <span>Assessment</span>
              </div>

              <strong>{title}</strong>
            </div>
          )}

          {summary && (
            <div className="privacy-completion-detail-row">
              <div className="privacy-detail-label">
                <span
                  className="privacy-detail-icon purple"
                  aria-hidden="true"
                >
                  ◉
                </span>

                <span>Summary</span>
              </div>

              <span>{summary}</span>
            </div>
          )}

          <div className="privacy-completion-detail-row">
            <div className="privacy-detail-label">
              <span
                className="privacy-detail-icon blue"
                aria-hidden="true"
              >
                □
              </span>

              <span>Case ID</span>
            </div>

            <strong>{caseId}</strong>
          </div>

          <div className="privacy-completion-detail-row">
            <div className="privacy-detail-label">
              <span
                className="privacy-detail-icon green"
                aria-hidden="true"
              >
                ♢
              </span>

              <span>Change ID</span>
            </div>

            <strong>{changeId}</strong>
          </div>

          <div className="privacy-completion-detail-row">
            <div className="privacy-detail-label">
              <span
                className="privacy-detail-icon purple"
                aria-hidden="true"
              >
                ◉
              </span>

              <span>Final status</span>
            </div>

            <span className="privacy-final-status">
              {statusLabel}
              <span aria-hidden="true"> ✓</span>
            </span>
          </div>
        </div>

        <div className="privacy-completion-divider" />

        <div className="privacy-completion-trust">
          <span
            className="privacy-completion-shield"
            aria-hidden="true"
          >
            ♢
          </span>

          <p>
            Thank you for helping EasyChatBot maintain
            <br className="desktop-only" />
            privacy, security, and trust.
          </p>
        </div>

        <button
          type="button"
          className="privacy-return-button"
          onClick={
            onReturnToCases ??
            (() => {
              window.location.href =
                "/privacy-governance";
            })
          }
        >
          <span aria-hidden="true">←</span>
          Return to Governance Cases
        </button>
      </section>
    </main>
  );
}