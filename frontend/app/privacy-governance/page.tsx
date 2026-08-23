"use client";

import { useParams } from "react-router-dom";

import PrivacyGovernanceDashboard from "../../components/privacy-governance/PrivacyGovernanceDashboard";

export const metadata = {
  title: "Privacy Governance Center | EasyChatBot",
  description: "Read-only privacy governance oversight.",
};

export default function PrivacyGovernancePage() {
  const { caseId } = useParams<{
    caseId?: string;
  }>();

  return (
    <PrivacyGovernanceDashboard
      initialCaseId={caseId}
    />
  );
}