export type GovernanceControl = {
  component: string;
  status: string;
  details: {
    paused?: boolean;
    reason?: string | null;
    changed_at?: string | null;
    [key: string]: unknown;
  };
};

export type GovernanceRecentEvent = {
  event: string;
  actor: string;
  reason: string;
  component: string;
  timestamp: string;
  severity?: "info" | "warning" | "critical" | string;
  evidence_available?: boolean;
};

export type GovernanceStatus = {
  yeti: {
    message: string;
  };
  controls: GovernanceControl[];
  recent_events: GovernanceRecentEvent[];
};

async function readJson<T>(response: Response, endpoint: string): Promise<T> {
  if (!response.ok) {
    throw new Error(
      `Governance API request failed (${response.status}) at ${endpoint}`,
    );
  }

  const contentType = response.headers.get("content-type") ?? "";

  if (!contentType.toLowerCase().includes("application/json")) {
    throw new Error(
      `Governance API returned non-JSON content at ${endpoint}. ` +
      `Check that the Vite proxy is running and FastAPI is available on port 8000.`,
    );
  }

  return response.json() as Promise<T>;
}

export async function getGovernanceStatus(): Promise<GovernanceStatus> {
  const endpoint = "/operations/governance/status";
  const response = await fetch(endpoint, {
    headers: { Accept: "application/json" },
  });

  return readJson<GovernanceStatus>(response, endpoint);
}
