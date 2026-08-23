# EasyChatBot Governance Change Lifecycle Integration

Vertical slice:

Approval Request
        |
        v
Approve / Reject
        |
        v
Change Record
        |
        v
GovernanceAuditService
        |
        v
Immutable Evidence
        |
        v
Operations Center + YETI

The integration keeps governance separate from execution.
Approval does not directly modify providers, models,
agents, or controls.
