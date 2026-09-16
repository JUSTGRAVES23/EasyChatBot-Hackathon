export async function getGovernanceStatus() {
  const response = await fetch("/operations/governance/status");
  if (!response.ok) throw new Error("Governance status unavailable");
  return response.json();
}

export async function getGovernanceTimeline() {
  const response = await fetch("/operations/governance/timeline");
  if (!response.ok) throw new Error("Governance timeline unavailable");
  return response.json();
}

export async function getProviderStatus() {
  const response = await fetch("/controls/providers/status");
  if (!response.ok) throw new Error("Provider status unavailable");
  return response.json();
}