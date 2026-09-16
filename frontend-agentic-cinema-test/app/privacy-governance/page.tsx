"use client";

import {
  useParams,
  useSearchParams,
} from "react-router-dom";

import PrivacyGovernanceDashboard from "../../components/privacy-governance/PrivacyGovernanceDashboard";
import PrivacyGovernanceCaseEntry from "../../components/privacy-governance/PrivacyGovernanceCaseEntry";

export const metadata = {
  title: "Privacy Governance Center | EasyChatBot",
  description: "Read-only privacy governance oversight.",
};

export default function PrivacyGovernancePage() {
  const { caseId: routeCaseId } = useParams<{
    caseId?: string;
  }>();

  const [searchParams] = useSearchParams();

  /*
   * There are intentionally two entry points:
   *
   * /privacy-governance
   *     → normal governance dashboard
   *
   * /privacy-governance/:caseId
   *     → email case-entry flow
   *
   * /privacy-governance?caseId=...
   *     → existing dashboard with the case drawer opened
   */

  if (routeCaseId) {
    return <PrivacyGovernanceCaseEntry />;
  }

  const queryCaseId =
    searchParams.get("caseId");

  return (
    <PrivacyGovernanceDashboard
      initialCaseId={queryCaseId}
    />
  );
}