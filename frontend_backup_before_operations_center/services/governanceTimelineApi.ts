export type GovernanceTimelineEvent = {
  event_id?: string;
  event: string;
  component: string;
  actor: string;
  reason: string;
  severity?: "info" | "warning" | "critical" | string;
  evidence_available?: boolean;
  timestamp: string;
};

export type GovernanceTimelineResponse = {
  events: GovernanceTimelineEvent[];
};

export async function getGovernanceTimeline(): Promise<GovernanceTimelineResponse> {
  const endpoint = "/operations/governance/timeline";

  const response = await fetch(endpoint, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(
      `Governance timeline request failed (${response.status}) at ${endpoint}`,
    );
  }

  const contentType = response.headers.get("content-type") ?? "";

  if (!contentType.toLowerCase().includes("application/json")) {
    throw new Error(
      `Governance timeline returned non-JSON content at ${endpoint}.`,
    );
  }

  return response.json() as Promise<GovernanceTimelineResponse>;
}
