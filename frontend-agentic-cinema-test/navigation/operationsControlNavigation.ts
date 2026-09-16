/**
 * Operations Control navigation definition.
 *
 * IMPORTANT:
 * Merge this into the EXISTING Operations Center navigation.
 * Do not render a second sidebar.
 */

export const operationsControlNavigation = {
  label: "OPERATIONS CONTROL",
  items: [
    {
      label: "Functionality Health",
      href: "/operations-center/functionality-health",
      icon: "activity",
      description: "Live health of EasyChatBot capabilities",
    },
    {
      label: "Email Workflows",
      href: "/operations-center/email-workflows",
      icon: "mail",
      description: "Email workflow health and controls",
      disabled: true,
    },
    {
      label: "Incidents",
      href: "/operations-center/incidents",
      icon: "alert-triangle",
      description: "Operational incidents and decisions",
      disabled: true,
    },
    {
      label: "Audit Trail",
      href: "/operations-center/audit",
      icon: "clipboard-list",
      description: "Administrative operational actions",
      disabled: true,
    },
  ],
} as const;
