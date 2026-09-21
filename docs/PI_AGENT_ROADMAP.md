# Platform Intelligence — Engineering Roadmap

## North-star capability

A user asks:

"Read the relevant platform screens and available governed information,
investigate the issue, assess it, provide evidence-backed findings,
identify gaps/risks, recommend actions, and escalate when defined
thresholds require human attention."

Target flow:

User question
→ Platform Intelligence Agent
→ InvestigationRequest
→ InvestigationPlan
→ Governed Skill selection
→ Screen/document/API/web/data Skills
→ Evidence
→ Cross-source analysis
→ Assessment
→ Per-output confidence
→ Quality Gate
→ Executive Report
→ Escalation decision
→ Human approval/action

## Milestone 0 — Runtime & Agent Foundation — BASELINE COMPLETE

- Runtime execution boundary exists.
- Provider Runtime exists.
- AgentFactory is generic.
- Project Manager and Platform Intelligence agents are registered.
- Investigation contracts exist.
- Output-level confidence contract exists.
- Skill manifest/loader/registry infrastructure exists.

## Milestone 1 — Governed Skill Execution — CURRENT

### PI-1A — Skill Infrastructure — COMPLETE

- SkillManifest governance contract.
- SkillLoader validation.
- SkillRegistry caching.
- Architecture Review Skill manifest.
- Skill contract tests.

### PI-1B — Governed Skill Execution — IN PROGRESS

Objective: execute one Runtime-authorised Skill through the existing execution
boundary.

Scope:
- Platform Intelligence PromptBuilder.
- Per-agent execution-service composition.
- SkillExecutionService.
- Skill resource loading.
- authorization/compatibility.
- architecture_review execution.
- result normalization.
- evidence/confidence safeguards.

Acceptance:
- inactive Skill rejected;
- incompatible agent rejected;
- unknown Skill rejected;
- Skill prompt safely resolved;
- no direct provider invocation;
- read-only execution;
- runtime regression green.

## Milestone 2 — Evidence & Investigation Engine

### PI-2A — Evidence-producing Skills

Implement governed:
- document discovery;
- document reading;
- URL/page reading;
- API/data retrieval;
- source metadata;
- authority;
- created/modified/retrieved/as-of dates;
- evidence IDs/provenance.

### PI-2B — Investigation Orchestration

Implement:
- plan execution;
- Skill-call/source/time budgets;
- deduplication;
- contradiction detection;
- evidence-gap detection;
- standard vs deep investigation.

## Milestone 3 — Platform Screen Intelligence

### PI-3A — Screen/page inventory

Inventory:
- route;
- screen ID;
- owner;
- domain;
- data source/API;
- sensitivity;
- authority;
- refresh characteristics;
- read capability;
- permission requirements.

### PI-3B — Screen Reading Skills

Implement governed Skills for:
- screen discovery;
- page data retrieval;
- dashboard metric extraction;
- control/status extraction;
- configuration/status inspection;
- document/page evidence extraction.

Do not use unrestricted UI scraping.

## Milestone 4 — Cross-Source Assessment

### PI-4A — Assessment Engine

Separate:
- facts;
- inference;
- recommendations;
- risk/impact;
- control gaps;
- confidence;
- evidence strength;
- authority.

### PI-4B — Quality Gate

Validate:
- evidence completeness;
- provenance;
- contradictions;
- confidence/evidence consistency;
- unsupported conclusions;
- required output sections;
- policy violations.

The LLM is not the final quality authority.

## Milestone 5 — Reporting

### PI-5A — Investigation Report

Produce:
- executive summary;
- scope/question;
- sources;
- evidence;
- findings;
- risks;
- evidence gaps;
- confidence;
- recommendations;
- human decisions;
- provenance appendix.

### PI-5B — Operations Center presentation

Expose read-only investigation results through Operations Center.
Keep presentation separate from investigation business logic.

## Milestone 6 — Escalation & Governance

### PI-6A — Escalation Policy

Configurable policy outcomes:
- `NO_ESCALATION`
- `REVIEW_RECOMMENDED`
- `HUMAN_REVIEW_REQUIRED`
- `URGENT_ESCALATION`

Inputs can include:
- severity;
- confidence;
- evidence sufficiency;
- control failure;
- compliance/security threshold;
- business impact;
- repeated failure;
- human-approval requirement.

### PI-6B — Human-in-the-loop

Implement:
- escalation record;
- reviewer;
- approve/reject;
- comments;
- audit trail;
- lifecycle;
- notification integration.

No autonomous consequential production remediation.

## Milestone 7 — Production Readiness

### PI-7A — Security/Governance

Review authorization, sensitive data, prompt injection, provider output,
Skill allowlists, budgets, audit, and side effects.

### PI-7B — Observability

Track investigation ID, agent, Skills, providers/models, latency, tokens/cost,
evidence/source counts, confidence, quality, escalation and failures.

## Milestone 8 — Demonstration

Target demonstration:

User question
→ PI investigates
→ reads authorised platform screens/data
→ collects evidence
→ cross-checks sources
→ assesses gaps/risks
→ produces executive report
→ confidence
→ Quality Gate
→ escalation if policy requires
→ human review.

## Explicitly deferred

- Kubernetes.
- Microservices.
- Vector DB/RAG platform.
- Autonomous production remediation.
- One Agent per Skill.
- Direct database access from agents.
- Direct provider SDKs in agents.
- Frontend-owned investigation logic.

## North-star Definition of Done

The capability is complete only when:
1. relevant authorised sources can be discovered;
2. governed Skills can read those sources;
3. evidence is traceable;
4. findings/inferences are separated;
5. material outputs have confidence;
6. evidence gaps are explicit;
7. Quality Gate runs before final reporting;
8. escalation is policy-driven;
9. human approval remains authoritative for consequential actions;
10. runtime/provider/agent boundaries remain intact;
11. security, regression, integration, E2E and smoke tests pass;
12. 4-eyes architecture/quality sign-off is complete.
