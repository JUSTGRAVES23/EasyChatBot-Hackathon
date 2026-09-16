export const governanceRoutes = {
  governanceCenter: "/operations-center/governance",

  privacyGovernance: "/privacy-governance",

  privacyGovernanceCase: (
    caseId: string,
  ): string =>
    `/privacy-governance/${encodeURIComponent(caseId)}`,
};