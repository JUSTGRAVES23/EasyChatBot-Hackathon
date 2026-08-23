# EasyChatBot Governance Change Management Core

This milestone generalises Change Management across the complete
AI Operations Center / Service Provider Management application.

Supported change domains:

- Provider
- Model
- Usage & Cost
- Escalation
- Quality
- Performance
- Agent
- Recommendation
- Reporting
- Configuration
- Security
- Scheduler
- Access
- Policy

Architecture boundary:

Recommendation
    |
    v
Change Request
    |
    v
Approval
    |
    v
Change Record
    |
    v
Governance Audit
    |
    v
Controlled Execution

Important:

ChangeManagementService records and governs changes.
It does NOT execute provider, model, agent, security,
scheduler, or configuration actions.
