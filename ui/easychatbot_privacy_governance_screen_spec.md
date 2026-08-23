# EasyChatBot Privacy Governance — Screen Design Specification

## Product role

Governance Operations Center screen for human DPO/GRC review. The screen is
decision-support and audit-oriented. It must never imply that email delivery
equals approval.

## EasyChatBot visual direction

Use the existing EasyChatBot product design system rather than introducing a
separate visual language.

Recommended visual hierarchy:
- Friendly, clean EasyChatBot surface.
- Rounded cards and restrained shadows.
- Clear typography and generous spacing.
- Use the existing EasyChatBot brand colours/tokens from the application.
- Primary action colour is reserved for controlled human actions.
- Status colours should be semantic: pending, approved, blocked/rejected.
- Do not make the governance screen look like a generic SOC console.

## Screen 1 — Governance Overview

Header:
- EasyChatBot branding
- "Privacy Governance"
- short subtitle: "Human review and privacy control evidence"

Summary cards:
- Pending DPO/GRC
- Approved
- Blocked
- Validation gaps
- Approval records

Pending table:
- Clickable Case ID
- Brief summary
- Trigger
- Trigger date/time
- Risk
- Validation
- Email status
- DPO/GRC status

The entire row may be clickable, but the Case ID must be visually obvious as the
stable navigation target.

## Screen 2 — Case Detail

Display:
- Case ID
- Title
- Brief summary
- Current governance status
- Risk
- Trigger type
- Triggered at
- Trigger source
- Processing IDs
- Data mapping IDs
- Automated validation result
- Email escalation result
- DPO decision
- GRC decision
- Final decision
- Final decision timestamp
- Approval history

Actions:
- Approve
- Reject
- Request changes

Human decision controls must show the reviewer identity and require a comment.

## Decision safety

Before enabling an approval action:
1. Show automated validation status.
2. Show applicable evidence links/identifiers.
3. Show outstanding reviewer roles.
4. Make clear that the action creates an auditable human decision.
5. Never use "Email sent" as an approval indicator.

## Navigation contract

The frontend should use:

`case_id -> case_detail(case_id)`

The backend view-model contract is provided by
`PrivacyGovernanceDashboardService.case_list()` and
`PrivacyGovernanceDashboardService.case_detail()`.

## Responsive behaviour

Desktop:
- summary cards in one row
- table with all governance columns
- detail view with evidence panels

Tablet/mobile:
- summary cards stack
- each case becomes a clickable card
- trigger, risk, validation and status remain visible
- approval actions remain prominent but separated from informational content
