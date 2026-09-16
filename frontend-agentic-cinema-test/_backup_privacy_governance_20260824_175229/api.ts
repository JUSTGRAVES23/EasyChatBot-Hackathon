import {
  privacyGovernanceEndpoints,
} from "./config";
import type {
  PrivacyGovernanceCase,
  PrivacyGovernanceStatusItem,
  PrivacyGovernanceSummary,
} from "./types";

async function requestJson<T>(url: string): Promise<T> {
  const response = await fetch(url, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(
      `Privacy governance API request failed (${response.status}).`,
    );
  }

  return response.json() as Promise<T>;
}

export function getPrivacyGovernanceSummary(): Promise<PrivacyGovernanceSummary> {
  return requestJson<PrivacyGovernanceSummary>(
    privacyGovernanceEndpoints.summary,
  );
}

export function getPrivacyGovernanceStatusChart(): Promise<
  PrivacyGovernanceStatusItem[]
> {
  return requestJson<PrivacyGovernanceStatusItem[]>(
    privacyGovernanceEndpoints.statusChart,
  );
}

export function getPrivacyGovernanceCases(): Promise<PrivacyGovernanceCase[]> {
  return requestJson<PrivacyGovernanceCase[]>(
    privacyGovernanceEndpoints.cases,
  );
}

export function getPrivacyGovernanceCase(
  caseId: string,
): Promise<PrivacyGovernanceCase> {
  return requestJson<PrivacyGovernanceCase>(
    privacyGovernanceEndpoints.caseDetail(caseId),
  );
}

export async function loadPrivacyGovernanceDashboard() {
  const [summary, statusChart, cases] = await Promise.all([
    getPrivacyGovernanceSummary(),
    getPrivacyGovernanceStatusChart(),
    getPrivacyGovernanceCases(),
  ]);

  return { summary, statusChart, cases };
}
