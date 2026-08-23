



# Cybersecurity Scheduler Email Integration


## Architecture


CybersecurityIntelligenceAgent
|
v
CybersecurityIntelligenceReportService
|
v
CybersecurityReportingIntegrationService
|
v
CybersecurityEmailService
|
v
Prepared Notification Payload


## Responsibilities



### Cybersecurity Intelligence Agent

Responsible for:

- analysing cybersecurity signals;
- calculating posture;
- prioritising risks.


### Intelligence Report Service

Responsible for:

- daily reports;
- weekly reports;
- critical event reports.


### Reporting Integration Service

Responsible for:

- workflow coordination;
- connecting approved services.


### Email Service

Responsible for:

- preparing communication payloads;
- future provider integration.


## Security Principles

- No autonomous remediation.
- No direct provider calls from agents.
- Human decision support only.
- Provider-independent design.