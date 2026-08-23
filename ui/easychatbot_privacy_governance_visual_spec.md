# EasyChatBot Privacy Governance — Visual Dashboard Specification

## Purpose

The Governance Operations Center provides an at-a-glance visual view of
privacy governance workload and status, while keeping every case clickable
and auditable.

## Dashboard

### KPI cards

Show:
- Total cases
- Pending DPO/GRC
- Approved
- Rejected / Blocked
- Validation failures

### Status chart

Include a donut/pie chart titled:

**Privacy Governance Case Status**

Segments:
- Pending DPO/GRC
- Approved
- Rejected / Blocked

The chart is informational only. It may filter the case list, but must never
change a case status.

### Clickable case list

Every case has a stable clickable identifier, for example `PCR-001`.

Display:
- Case ID
- Brief summary
- Trigger
- Triggered date/time
- Risk
- Validation
- Email
- Governance status
- Final decision
- Decision date

Mobile converts rows into clickable case cards without removing the key fields.

### Case detail

Show:
- Case identifier
- Trigger information
- Processing/data-map references
- Validation evidence
- Email escalation status
- DPO decision
- GRC decision
- Final decision
- Final decision timestamp
- Approval history

## EasyChatBot branding

Use the existing EasyChatBot application design system and brand tokens.
Do not create a separate SOC/compliance visual language.

Recommended:
- EasyChatBot branded header
- rounded cards
- generous spacing
- professional, friendly typography
- semantic status badges
- restrained warning colours
- strong distinction between information and decision controls

## Chart data contract

The backend exposes:

```json
[
  {"status": "Pending DPO/GRC", "count": 3},
  {"status": "Approved", "count": 12},
  {"status": "Rejected / Blocked", "count": 2}
]
```

These numbers are illustrative only. Production values must come from
`PrivacyGovernanceDashboardService.status_chart()`.

## Governance safety

The chart is never approval evidence. The authoritative decision is the
case-level governance record and explicit human approval/rejection record.
