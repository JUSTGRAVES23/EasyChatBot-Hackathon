# CODEX M0 Architecture Discovery

Status: M0 discovery only. No production implementation is authorized by this document.

Repository inspected: `C:/AI Folder/EasyChatBot-Hackathon`

Source pack inspected: `C:/Users/barbe/Downloads/EasyChatBot_Privacy_Governance_CODEX_FINAL_SOURCE_PACK_v1.0`

Generated scope: architecture discovery, gap classification, reuse recommendation, and STOP register for the EasyChatBot Privacy and Fundamental Rights Governance framework.

## 1. Repository Reality Map

The repository already contains several governance-related bounded contexts. The M0 implementation path must preserve these boundaries instead of creating a duplicate privacy governance platform.

| Area | Reality | Evidence | M0 classification |
|---|---|---|---|
| Application entry point | `backend/app/main.py` is the Academy FastAPI composition root used by `run_backend.py` and many tests. It composes repositories, runtime services, questionnaire runtime, authentication, CMP operations routes, and AI Operations Center routes. | `backend/app/main.py`, `run_backend.py`, `run_server.py` | Existing capability that should be reused. |
| Privacy/GRC operational layer | `backend/app/application/privacy` contains Beta 1-scoped privacy governance models, registries, validation, gating, case lifecycle, DPO/GRC decision handling, dashboard projection, Excel projection, and reminder email support. | `backend/app/application/privacy/*` | Existing capability that should be reused and extended cautiously. |
| Canonical privacy governance API file | `backend/app/api/privacy_governance.py` declares a single canonical router at `/api/privacy/governance`, with read endpoints, decision endpoints, and a demo case endpoint. | `backend/app/api/privacy_governance.py` | Existing capability requiring architecture decision because it is not visibly registered in `backend/app/main.py`. |
| General governance backend | `backend/governance` contains enterprise change management, approval, audit, evidence, timeline, and operations-center projection services. | `backend/governance/*` | Existing capability with overlap. Do not merge silently. |
| Operations Center UI/backend | `frontend/components/operations-center`, `frontend/services/governanceApi.ts`, and `backend/governance/api/*` support a general governance center at `/operations-center/governance`. | `frontend/components/operations-center/README_GOVERNANCE_CENTER.md`, `backend/governance/api/*` | Existing separate bounded context. |
| Privacy governance UI | `frontend/components/privacy-governance`, `frontend/lib/privacy-governance`, and `frontend/app/privacy-governance/page.tsx` implement a privacy governance dashboard, case drawer, and explicit decision submission UI. | `frontend/components/privacy-governance/*`, `frontend/lib/privacy-governance/*` | Existing capability requiring integration verification. |
| Persistence | Alembic migrations exist for users, beta access, conversation events, conversation privacy fields, auth roles/tokens, publication state, and announcement approval audit events. No privacy governance case/approval/evidence database tables were found in migration sweep. | `backend/alembic/versions/*`, `backend/app/infrastructure/persistence/*` | Existing persistence capability, but privacy governance persistence is genuinely missing if durable privacy cases are required. |
| Workbooks | `privacy_governance_tracker.xlsx` is represented in source pack and via Excel sync code as downstream evidence/reporting projection. `EasyChatBot_Beta1_Privacy_GRC_DPO_Workbook.xlsx` exists as a DPO/GRC reference workbook in source pack and repo docs. | Batch 03 workbooks, `backend/app/application/privacy/privacy_governance_excel_sync.py`, `docs/privacy/beta1/*` | Reference/projection artifacts; not authoritative runtime stores. |
| Legal/regulatory sources | Batch 04 contains source handling rules, EDPB-style DPIA template, FRIA Article 27 template, and FRIA questionnaire. No standalone Legal Source Register file was found. | Batch 04 files | Legal source register capability is missing/pending; legal applicability decisions are unresolved. |

## 2. Existing Privacy/GRC Components

### Privacy operational package

`backend/app/application/privacy` is the primary existing privacy/GRC package. It is explicitly described as a Beta 1 governance/evidence boundary and not a substitute for legal advice, formal ROPA, privacy notice, DPIA, contracts, or DPO approval.

Key components:

| Component | Purpose | M0 treatment |
|---|---|---|
| `ProcessingActivity` | Machine-readable Beta 1 processing activity with purpose, data categories, data subjects, sources, destinations, legal basis, retention, processors, data map, DPIA screening, GDPR references, controls, metadata, and approval status. | Reuse as existing processing anchor. |
| `ProcessingActivityRecord` | ROPA-oriented record with controller role, recipients, processors, systems, transfer status, retention, security measures, lawful basis, legal references, and draft status. | Reuse/extend for ROPA-style reporting; do not duplicate. |
| `ProcessingRegistry` | Deterministic Beta 1 processing activity registry; governance input, not legal approval engine. | Reuse; repository-backed implementation may be later milestone. |
| `DataProcessingMapEntry` / `DataProcessingMap` | Operational data flow representation for one processing activity, including source, input data, runtime processing, persistence, destinations, third-country transfer, and safeguard. | Reuse for Data Flow; keep distinct from Processing Activity. |
| `RetentionRule` / `RetentionRegistry` | Retention rule registry. | Reuse/extend for retention evidence. |
| `ProcessorRecord` / `ProcessorRegistry` | Processor/vendor facts including provider, role, Art. 28 agreement status, hosting location, third-country flag, safeguard, and DPO/GRC/legal status. | Reuse; distinguish processor from recipient. |
| `DPIAScreening` / `DPIAScreeningRegistry` | Screening record only: overall risk, `dpia_required`, DPO/GRC assessment, status. | Reuse for screening; do not treat as full DPIA. |
| `PrivacyValidationService` | Deterministic consistency validation for required governance evidence. It never makes legal decisions or grants approval. | Reuse as pre-gate validation, extend only with deterministic evidence checks. |
| `PrivacyChange`, `PrivacyChangeDetector`, `PrivacyChangeAssessmentService`, `PrivacyChangeRegistry` | Privacy change-control descriptors, detection, deterministic routing aid, and in-memory registry. | Reuse/extend for lifecycle triggers. |
| `PrivacyGovernanceGate` | Routes privacy-impacting changes, blocks validation failures, triggers escalation, and never treats email as approval. | Reuse as governance gate. |
| `PrivacyGovernanceCase`, `PrivacyGovernanceCaseService`, `PrivacyGovernanceCaseRegistry` | Case-centric governance review item and lifecycle. | Reuse as Governance Case; extend only after architecture decision. |
| `PrivacyApprovalRecord`, `PrivacyApprovalRegistry`, `PrivacyGovernanceDecisionService` | Immutable human DPO/GRC decision evidence and decision state transitions. | Reuse for DPO/GRC decision evidence; do not replace. |
| `PrivacyEvidenceRecord` | Evidence item with source system, control reference, legal references, status, owner, and metadata. | Reuse for evidence; distinguish from control definition and approval. |
| `PrivacyGovernanceDashboardService` / `PrivacyGovernanceDashboardAPI` | Read-only projection for UI/API. | Reuse as read model. |
| `PrivacyGovernanceExcelSync` / tracker projection | Downstream Excel reporting/evidence projection; registries stay authoritative. | Reuse as projection only. |
| Reminder email scheduler/services | Reminder/escalation support for pending DPO/GRC decisions; notification only. | Reuse if reminders remain in scope; not approval. |

### General governance package

`backend/governance` contains a broader enterprise governance context:

| Component | Purpose | M0 treatment |
|---|---|---|
| `ChangeRecord`, `ChangeManagementService` | Enterprise change records for provider/model/agent/config/security/scheduler changes. | Existing overlap with `PrivacyChange`; architecture decision required before integrating. |
| `ApprovalRequest`, `ApprovalService` | Generic approval request lifecycle. | Existing overlap with privacy approval; do not duplicate or merge silently. |
| `GovernanceAuditService`, `AuditEvent` | In-memory audit/evidence collection boundary. | Reuse pattern or bridge after architecture decision. |
| `GovernanceEvidenceService`, timeline/dashboard services | Read-only Operations Center projections. | Existing operations visibility context. |
| `backend/governance/api/*` | General governance API routes. | Separate from privacy governance API unless architecture decision merges route composition. |

## 3. Existing Domain Entities

### Privacy domain entities

| Entity | Fields or meaning | Current persistence |
|---|---|---|
| `ProcessingActivity` | Processing ID, name, purpose, data categories, data subjects, source, destinations, legal basis, retention ID, processor IDs, data map ID, DPIA screening ID, GDPR references, security controls, metadata, approval status. | In-memory registry. |
| `ProcessingActivityRecord` | ROPA-oriented processing activity with controller role, recipients, processors, systems, transfer status, lawful basis, legal references, status. | In-memory/documentation-oriented. |
| `DataProcessingMapEntry` | Per-processing operational flow: source, input data, runtime processing, pseudonymisation, persistence, destinations, transfer flag/safeguard. | In-memory registry. |
| `RetentionRule` | Data domain, record type, retention period, trigger, deletion action, legal/policy basis. | In-memory registry. |
| `RetentionClassification` | Classification, domain, type, period, trigger, review action, deletion action, legal/policy reference, owner, draft status. | In-memory/object only. |
| `ProcessorRecord` | Processor/vendor facts, Art. 28 status, hosting/transfer/safeguard statuses, DPO/GRC/legal review statuses. | In-memory registry. |
| `DPIAScreening` | Screening ID, processing ID, overall risk, DPIA required flag/value, DPO/GRC assessment, status. | In-memory registry. |
| `PrivacyChange` | Change descriptor and flags for affected processing, categories, purpose, recipients, retention, processor, transfer, automated decision, DPIA screening, risk, DPO/GRC required, status. | In-memory registry. |
| `PrivacyChangeDetection` / `PrivacyChangeAssessment` | Deterministic routing result; not legal decision. | Computed. |
| `PrivacyGovernanceCase` | Case ID, trigger, linked change ID, processing/data map IDs, risk, validation/email/governance status, final decision/time. | In-memory registry. |
| `PrivacyApprovalRecord` | Approval ID, case/change ID, reviewer, role, decision, comment, timestamp. | In-memory registry; Excel projection. |
| `PrivacyEvidenceRecord` | Evidence ID, activity ID, type, description, source system, control reference, legal references, collected timestamp, owner, status, metadata. | In-memory/object only. |
| `PrivacyGovernanceReminderRecord` and related reminder result/policy types | Reminder history and non-binding decision support. | In-memory/test-focused. |

### Conversation/analytics-adjacent entities

| Entity | Meaning | Current persistence |
|---|---|---|
| `ConversationEvent` | Pseudonymous learner identity, conversation session, world, channel, role, content, metadata, created timestamp. It explicitly excludes Telegram ID, email, and direct identity. | PostgreSQL `conversation_events`. |
| `ConversationEventRecord` | SQLAlchemy persistence model for `conversation_events`, including pseudonymous identity, content, metadata JSON, privacy hash version, retention policy ID. | PostgreSQL. |
| `ConversationEventValidator` | Fails events without pseudonymous identity, metadata, retention classification, or with forbidden identity/context strings. | Computed before persistence. |
| `PrivacyIdentifierService` | HMAC pseudonymisation for sensitive identifiers; not authentication or authorization. | Stateless service. |

### Authentication/authorization entities

| Entity | Meaning | Current persistence |
|---|---|---|
| `easychatbot_session` cookie | Server-side HttpOnly Secure SameSite=Lax session cookie. | `user_sessions` via auth repository. |
| `Principal`, `Role`, `Permission` | Existing auth/RBAC concepts. Current permission enum has announcement permissions only. | Auth repository plus static permission map. |

## 4. Database/Repository Boundaries

### Existing database tables discovered

The Alembic sweep found tables for:

- `users`
- `worlds`
- `events`
- `learning_worlds`
- `beta_users`
- `telegram_bindings`
- `beta_connection_tokens`
- `conversation_events`
- `auth_user_roles`
- `auth_email_verification_tokens`
- `announcement_publications`
- `announcement_publication_executions`
- `announcement_publication_audit_events`
- `announcement_publication_approval_audit_events`
- `academy_notification_deliveries`

No Alembic migration was found for privacy governance case, privacy approval, privacy evidence, Processing Activity/RoPA, DPIA, FRIA, TIA, Legal Source Register, processor/vendor governance, or retention register tables.

### Current privacy persistence boundary

The active privacy governance runtime uses in-memory registries:

- `PrivacyChangeRegistry`
- `PrivacyGovernanceCaseRegistry`
- `PrivacyApprovalRegistry`
- `ProcessingRegistry`
- `DataProcessingMap`
- `RetentionRegistry`
- `ProcessorRegistry`
- `DPIAScreeningRegistry`

`PrivacyGovernanceComposition` says Beta 1 uses in-memory registries and that repository-backed implementations can replace registries later without changing application service contracts.

### Excel boundary

`PrivacyGovernanceExcelSync` writes three projection sheets:

- `Privacy Governance Cases`
- `Approval Evidence`
- `Governance Dashboard`

The sync code states that the registries remain authoritative and Excel cannot change governance state. This matches Batch 03 and must be preserved.

### Material persistence gaps

| Gap | Classification | Required decision |
|---|---|---|
| Durable privacy governance case/approval/evidence storage | Genuinely missing capability if production durability is required. | Architecture decision on repository-backed registries and database ownership. |
| Durable Processing Activity/RoPA/register storage | Existing capability requiring extension if current in-memory registry is insufficient. | Architecture and DPO/GRC decision on authoritative record source. |
| Durable Legal Source Register | Genuinely missing capability. | Legal/governance decision on source register ownership and approval process. |
| Durable DPIA/FRIA/TIA records | Genuinely missing capability for full assessments; DPIA screening exists. | Legal applicability and architecture decisions required before schema. |

## 5. Existing Privacy UI

The active privacy UI surface is:

- `frontend/app/privacy-governance/page.tsx`
- `frontend/lib/privacy-governance/config.ts`
- `frontend/lib/privacy-governance/api.ts`
- `frontend/lib/privacy-governance/decision-api.ts`
- `frontend/lib/privacy-governance/types.ts`
- `frontend/components/privacy-governance/PrivacyGovernanceDashboard.tsx`
- `frontend/components/privacy-governance/PrivacyGovernanceCaseDetail.tsx`
- `frontend/components/privacy-governance/PrivacyGovernanceDecisionActions.tsx`
- `frontend/components/privacy-governance/PrivacyGovernanceCaseEntry.tsx`
- `frontend/components/privacy-governance/PrivacyGovernanceAssessmentResult.tsx`
- related CSS modules.

Capabilities already present:

- dashboard loading for summary, status chart, and cases;
- filterable case table;
- case detail drawer;
- approval evidence display;
- explicit decision submission with role, reviewer, rationale, confirmation dialog;
- client-side guard for missing `change_id`;
- support for approve, reject, and request changes.

Material UI conflicts or ambiguities:

| Issue | Classification | M0 action |
|---|---|---|
| `frontend/app/privacy-governance/page.tsx` uses `react-router-dom` hooks under an `app` path, which may or may not match the active frontend router/runtime. | Existing capability requiring verification. | Verify active frontend framework and route ownership before extending. |
| Privacy UI points to `/api/privacy/governance`, but `backend/app/main.py` did not visibly include the privacy router. | Material architecture conflict. | STOP implementation until API composition decision is made. |
| Existing Operations Center governance screen already uses `/operations-center/governance` and general governance endpoints. | Duplicate/overlap risk. | Do not create another governance center without architecture decision. |

## 6. Consent/Analytics Architecture

### Authentication and consent are separate

Authentication currently uses the `easychatbot_session` cookie set by `backend/app/api/authentication.py` with `httponly=True`, `secure=True`, and `samesite="lax"`. Session identity is resolved through `backend/app/api/dependencies/identity.py` and `SessionIdentityProvider`.

No consent management runtime, cookie banner, consent registry, or consent preference store was found in the inspected active source paths.

Classification: consent management is a genuinely missing capability if required by later milestones, but it must not be implemented by changing authentication/session semantics.

### Analytics and learning data are separate

The repository has `conversation_events`, which are not a generic product analytics event store. The domain and persistence comments say they store pseudonymous conversation events and may feed future Memory Engine, Learning Intelligence, RAG pipelines, analytics, quality evaluation, and conversation improvement.

Important reality:

- `ConversationEvent` stores `content`.
- `ConversationEventValidator` forbids some raw identity/context strings and requires metadata including `retention_policy_id`.
- `ConversationEventRecord` stores pseudonymous identity, content, metadata JSON, privacy hash version, and retention policy ID.
- Batch 05 forbids analytics payloads containing full learner conversations, exact learner text unless separately approved, voice recordings, Telegram content, cookies, credentials, tokens, secrets, unnecessary direct identifiers, or unrestricted personal-data payloads.

Classification:

| Topic | Reality | M0 classification |
---|---|---|
| Product/operational analytics event contract | No dedicated source-path implementation found. | Genuinely missing capability if required. |
| Conversation learning event storage | Exists as `conversation_events`. | Existing capability to reuse only for learning/conversation events, not as generic analytics. |
| Analytics payload validation | Partial privacy validation exists for conversation events; Batch 05 requires fail-closed analytics validation for prohibited payloads. | Existing capability requiring extension or a new boundary decision, not a duplicate data store. |
| Consent treatment for optional analytics | Not found. | Governance/legal decision required. |

## 7. Reality to Semantic Model Mapping

| Semantic concept | Current repository representation | Mapping status | Gap classification |
|---|---|---|---|
| Processing Activity | `ProcessingActivity`, `ProcessingActivityRecord`, `ProcessingRegistry`; docs `docs/privacy/ROPA.md`; workbook ROPA sheet. | Partially represented. | Existing capability requiring extension for full platform/durable authority. |
| Data Flow | `DataProcessingMapEntry`, `DataProcessingMap`; workbook `Data_Processing_Map`. | Represented separately from Processing Activity. | Existing capability should be reused. |
| DPIA Screening | `DPIAScreening`, `DPIAScreeningRegistry`; workbook `DPIA_Screening`. | Represented. | Existing capability should be reused. |
| DPIA | No full DPIA domain found; EDPB template and DPO comments exist as Batch 04 sources. | Not implemented beyond screening/reference material. | Genuinely missing capability; legal decision required per processing. |
| FRIA | No active FRIA model/API/UI found in checked source paths; Batch 04 template and questionnaire exist. | Not implemented. | Genuinely missing capability, but Article 27 applicability requires legal/classification gate. |
| TIA / transfer assessment | Transfer flags/safeguards exist in `ProcessorRecord` and `DataProcessingMapEntry`; no TIA methodology/model found. | Partial facts only. | Existing capability requiring extension; legal decision required; do not invent methodology. |
| Risk | `PrivacyChangeRisk`, case `risk`, DPIA screening `overall_risk`, general governance `ChangeRisk`. | Multiple risk representations. | Existing capabilities requiring reconciliation. |
| Mitigation/control | Security controls fields exist on processing activity; evidence has `control_reference`; no full control catalog found. | Partial. | Existing capability requiring extension if control library is required. |
| Evidence | `PrivacyEvidenceRecord`, `PrivacyApprovalRecord`, Excel `Approval Evidence`, general governance audit/evidence service. | Partially represented. | Existing capabilities should be reused; define authoritative source. |
| DPO Review | DPO role in approval records/UI; DPO comments in DPIA template. | Partially represented. | Existing capability requiring extension to separate review/advice from decision. |
| Governance Decision | `PrivacyGovernanceDecisionService`, `PrivacyApprovalRecord`, case `final_decision`, decision UI. | Represented. | Existing capability should be reused. |
| Governance Case | `PrivacyGovernanceCase`, case service/registry/dashboard. | Represented. | Existing capability should be reused. |
| Privacy Change | `PrivacyChange`, detector, assessment, gate, flow service. | Represented. | Existing capability should be reused. |
| Processor | `ProcessorRecord`, `ProcessorRegistry`, legacy `ProcessorRegistryService`. | Represented, with duplicate/older variant. | Existing capability requiring consolidation decision. |
| Recipient | `ProcessingActivityRecord.recipients`, `PrivacyChange.recipients_changed`; no recipient registry found. | Partial. | Existing capability requiring extension if recipient governance is required. |
| Consent | No consent runtime/register found; workbook/legal docs reference consent choices. | Not implemented. | Genuinely missing, legal decision required. |
| Authentication | Existing auth/session cookie and auth repository. | Represented. | Existing capability must be preserved; do not repurpose as consent. |
| Analytics Data | Conversation events and operational telemetry exist; product analytics contract not found. | Partial/ambiguous. | Existing capability requiring boundary decision. |
| Learning Data | Conversation events, memory, learning-world/event infrastructure. | Represented separately from analytics policy. | Existing capability should be reused; do not treat analytics as learning memory. |
| Legal Source Register | No standalone file or runtime model found. | Missing. | Genuinely missing; legal/governance decision required. |
| Assessment Passport/Health | No dedicated implementation found. | Missing. | Existing UI/dashboard may be extended after architecture decision. |

Required distinctions preserved:

- Processing Activity is not Data Flow.
- DPIA Screening is not DPIA.
- DPIA is not FRIA.
- Processor is not Recipient.
- Control is not Evidence.
- DPO Review is not Governance Decision.
- Consent is not Authentication.
- Analytics Data is not Learning Data.

## 8. Reality to Master Specification Mapping

Target lifecycle from Batch 01:

`Processing Activity -> Screening -> DPIA / FRIA / TIA -> Risk -> Mitigation -> Evidence -> DPO Review -> Governance Decision -> Monitoring -> Reassessment`

| Lifecycle stage | Repository reality | Status | Gap classification |
|---|---|---|---|
| Processing Activity | `ProcessingActivity`, `ProcessingActivityRecord`, `ProcessingRegistry`. | Partial. | Existing capability requiring extension/durability. |
| Screening | `DPIAScreening`; `PrivacyChangeAssessmentService` also routes privacy changes and flags DPIA screening. | Partial. | Existing capability should be reused and extended. |
| DPIA | Only DPIA Screening plus templates/workbooks/docs. | Missing. | Genuinely missing; legal decision required. |
| FRIA | No active implementation found. | Missing. | Genuinely missing; Article 27 applicability decision required first. |
| TIA | Transfer facts/safeguards exist; no assessment methodology. | Partial. | Existing capability requiring extension; legal decision required. |
| Risk | Privacy and general governance risk enums/statuses; DPIA sample risk tables. | Partial. | Existing capability requiring reconciliation. |
| Mitigation | Security controls and evidence references exist; no full mitigation/action plan model. | Partial. | Existing capability requiring extension. |
| Evidence | Approval/evidence records, Excel projection, general audit events. | Partial. | Existing capability should be reused and made authoritative. |
| DPO Review | DPO role and workbook/DOCX comments exist; no distinct DPO advice lifecycle. | Partial. | Existing capability requiring extension; preserve distinction from decision. |
| Governance Decision | Decision service/API/UI exists. | Represented. | Existing capability should be reused. |
| Monitoring | Reminder scheduler and dashboards exist; no assessment-health monitoring found. | Partial. | Existing capability requiring extension. |
| Reassessment | Change detector has reassessment trigger dimensions but no full reassessment lifecycle. | Partial. | Existing capability requiring extension. |

Master specification constraints that match repo:

- Avoid duplicate systems: existing code repeatedly marks registries as authoritative and Excel as projection.
- Preserve architecture: composition root and repository contracts are established patterns.
- Separate governance from AI runtime: Operations Center docs and app main both emphasize read-only/control boundaries.
- Separate analytics from learning/memory: source pack requires it; repo currently has conversation events that can feed analytics/learning but not a dedicated analytics contract.

Master specification requirements needing repository verification or decisions:

- Whether privacy governance router is active in the real app composition.
- Whether current frontend route structure is valid for the active frontend runtime.
- Whether privacy governance needs durable database persistence before any production use.
- Whether Legal Source Register must be created as docs-only first or as model-backed runtime metadata.
- Whether FRIA is statutory Article 27 workflow, broader internal FRIA, or both.
- Whether TIA requires only transfer fact tracking or an approved legal methodology.
- Whether RBAC needs privacy-specific permissions or can reuse existing Operations Center auth.

## 9. Workbook to Repository Reconciliation

### `privacy_governance_tracker.xlsx`

| Workbook concept | Workbook evidence | Repository mapping | Authority | M0 classification | Smallest safe integration |
|---|---|---|---|---|---|
| Privacy Governance Cases | Sheet `Privacy Governance Cases` with case/change/title/trigger/risk/validation/governance/email/final decision/processing IDs/data map IDs. | `PrivacyGovernanceCase`, `PrivacyGovernanceCaseRegistry`, `PrivacyGovernanceCaseService`, `PrivacyGovernanceDashboardService`, `PrivacyGovernanceExcelSync`. | Runtime registries authoritative; workbook projection only. | Existing capability should be reused. | Keep Excel as downstream projection; do not import workbook as source of state. |
| Approval Evidence | Sheet `Approval Evidence` with approval ID, case ID, change ID, reviewer, role, decision, comment, decided at. | `PrivacyApprovalRecord`, `PrivacyApprovalRegistry`, `PrivacyGovernanceDecisionService`. | Runtime approval registry authoritative; workbook projection only. | Existing capability should be reused. | Preserve one-way sync from registry to workbook. |
| Governance Dashboard | Sheet `Governance Dashboard` with totals/pending/approved/blocked/approval records/last sync. | `PrivacyGovernanceDashboardService.summary()` and Excel sync dashboard. | Runtime read model authoritative. | Existing capability should be reused. | Keep dashboard derived from cases/approvals. |

### `EasyChatBot_Beta1_Privacy_GRC_DPO_Workbook.xlsx`

| Workbook concept | Repository mapping | Authority | M0 classification | Pending/TBD fields |
|---|---|---|---|---|
| ROPA_Beta1 | `ProcessingActivityRecord`, `ProcessingActivity`, `ProcessingRegistry`, docs `docs/privacy/ROPA.md`. | Workbook is reference/DPO review artifact; runtime registry is current implementation source. | Existing capability requiring extension. | Legal basis, controller/processor roles, transfer, retention, approval statuses. |
| Legal_Basis_Assessment | `ProcessingActivity.legal_basis`, `ProcessingActivityRecord.lawful_basis`, validation checks legal basis. | Legal/DPO decision, not code. | Requirement needing legal decision. | Selected Art. 6 bases and DPO/legal statuses. |
| Data_Processing_Map | `DataProcessingMapEntry`, `DataProcessingMap`. | Repository map should be authoritative when implemented; workbook reference. | Existing capability should be reused. | Provider transfer details and exact processing facts. |
| Retention_Register | `RetentionRule`, `RetentionClassification`, `RetentionRegistry`, conversation event `retention_policy_id`. | DPO/GRC/legal signoff required. | Existing capability requiring extension. | Retention periods/triggers/signoff. |
| Processor_Transfer_Register | `ProcessorRecord`, `ProcessorRegistry`; legacy `ProcessorRegistryService` also exists. | Repository should own processor facts after architecture decision. | Existing capability requiring reconciliation. | Art. 28, transfer mechanism, legal status. |
| DPIA_Screening | `DPIAScreening`, `DPIAScreeningRegistry`. | Repository screening model can represent it; DPO/legal decides outcome. | Existing capability should be reused. | Whether DPIA required and approved. |
| Legal_Article_Register | No legal source register implementation found; privacy README references workbook articles and EUR-Lex as draft source. | Legal source register missing. | Genuinely missing capability; legal decision required. | Article applicability, source version, approved interpretation. |
| DPO_GRC_Signoff | `PrivacyApprovalRecord`, `PrivacyGovernanceDecisionService`, `PrivacyGovernanceCase`. | Runtime decision records authoritative when connected to active flow; workbook/signoff doc reference until productionized. | Existing capability requiring extension. | Actual names, approvals, conditions. |

Conflicts/overlaps:

- Workbooks contain sample or pending legal fields; do not convert `TBD` or `PENDING` into implementation defaults.
- `privacy_governance_tracker.xlsx` overlaps with runtime case/approval registries but is explicitly a projection.
- `EasyChatBot_Beta1_Privacy_GRC_DPO_Workbook.xlsx` overlaps with code models but is a DPO/GRC reference artifact, not a database.

## 10. Legal Source Dependency Map

| Source | Source type | Authority level | Version/date | Requirement or concept informed | Repository/spec impact | Applicability question | Unresolved legal decision |
|---|---|---|---|---|---|---|---|
| Batch 04 `LEGAL_SOURCE_HANDLING.md` | Internal source-handling rule | Internal governance control | File timestamp 2026-09-05 | Provenance, version/date tracking, law/guidance/template/questionnaire distinction, no inferred conclusions, DPO decision points. | M0 must preserve legal source provenance and unresolved decisions. | Is there an approved Legal Source Register outside the pack? | Legal owner must approve authoritative legal sources. |
| EDPB DPIA template DOCX | Regulatory template/guidance material plus sample completion and DPO comments. | High guidance/template value, but template structure is not itself a production requirement. | Version table: 1.0, 10 March 2026; file created/modified 2026-04-14. | DPIA structure, necessity/proportionality, risk, mitigation, DPO advice, decision, evidence expectations. | Supports future DPIA module mapping; current repo has DPIA screening only. | Is an Article 35 DPIA required for each EasyChatBot processing activity? | DPO/legal must decide DPIA trigger, adequacy, acceptance, and prior consultation. |
| DPO comments in EDPB DPIA DOCX | DPO review/challenge comments | Review input, not final decision | Comments dated 2026-05-17 | LIA evidence, less intrusive alternatives, proxy-variable testing, Canadian support access, retention split, meaningful human review, go-live blockers, evidence links. | Can inform evidence checklist only after applicability mapping. | Which comments apply to EasyChatBot versus the sample credit-scoring scenario? | DPO review/advice must remain distinct from governance decision. |
| FRIA Article 27 template DOCX | Practical FRIA template | Template/internal implementation aid referencing EU AI Act Article 27 | Modified 2026-09-05; references CEDPO January 2025 and EU AI Act Article 27 | High-risk classification, deployer context, affected groups, EU Charter rights mapping, risk methodology, safeguards, approvals, monitoring, DPIA alignment. | No FRIA implementation found; supports future design only after applicability decision. | Is EasyChatBot a deployer of a high-risk AI system covered by Article 27? | AI Act classification and Article 27 applicability. |
| `FRIA_questionnaire.xlsx` | Internal questionnaire / decision-support workbook | Lower than law/guidance; not law | File timestamp 2026-09-05 | Applicability questions, Annex III categories, deployer/provider distinction, affected groups, fundamental rights, mitigation, human oversight, DPIA alignment, reporting. | Can become questionnaire logic only after governance approval. | Which rows apply to statutory FRIA versus broader internal FRIA? | Legal/compliance must approve question logic and any scoring/routing. |
| Batch 05 analytics event data policy | Internal implementation rule | Source-pack rule for implementation | File timestamp 2026-09-05 | Allowed, forbidden-by-default, and conditional analytics data categories; fail-closed validation requirement. | Requires analytics event boundary check before using existing conversation events or adding telemetry. | Which analytics events are approved and under what lawful basis/consent treatment? | Consent/lawful basis, retention, access, and governance approval for analytics events. |
| GDPR Chapter V / transfer requirements as referenced by templates/workbooks | Law/regulatory requirement references | Legal requirement, but source pack does not provide full legal text or approved TIA method. | Not independently versioned in Batch 04. | Processor/transfer facts and safeguards. | Existing processor and data-flow models capture transfer flags/safeguards; no TIA method found. | Are there third-country transfers or remote support access in actual processing? | Transfer mechanism/TIA methodology must be legally approved; do not invent. |
| EU AI Act Article 27 / Annex III references | Law/regulatory requirement references | Legal requirement, but M0 did not independently validate consolidated legal text. | Referenced in FRIA docs; not full standalone legal source. | Statutory FRIA applicability and high-risk/deployer classification. | Requires classification gate before FRIA lifecycle. | Does Article 27 apply to this system/use case/entity? | Legal classification decision. |

Required distinctions:

- DPIA legal requirements are not the same as the EDPB template field structure.
- AI Act Article 27 FRIA applicability is not the same as a broader internal FRIA.
- Internal questionnaire logic is not law.
- Transfer requirements are not an invitation to invent a TIA methodology.

## 11. Reuse Map

| Requirement area | Reuse first | Extend only if | Do not build |
|---|---|---|---|
| Processing/RoPA | `ProcessingActivity`, `ProcessingActivityRecord`, `ProcessingRegistry`, docs/workbook mapping. | Durable platform-wide registry is approved. | New parallel ROPA system. |
| Data flow | `DataProcessingMapEntry`, `DataProcessingMap`. | More stages/recipients/processors need normalized representation. | Data-flow model embedded inside DPIA only. |
| DPIA screening | `DPIAScreening`, existing validation/gate links. | Screening questions require approved expansion. | Full DPIA disguised as screening. |
| DPIA | Current screening plus Batch 04 template mapping. | Legal decides DPIA is required and architecture approves module ownership. | New standalone DPIA engine before mapping to existing concepts. |
| FRIA | Reuse governance case/change/evidence/risk/decision patterns. | Article 27/internal FRIA scope is decided. | FRIA as duplicate governance case or duplicate approval system. |
| TIA/transfer | `ProcessorRecord`, `DataProcessingMapEntry.transfer_safeguard`, workbook processor/transfer register. | Legal approves transfer methodology and facts. | Invented TIA scoring/method. |
| Risk/mitigation | `PrivacyChangeRisk`, case risk, `PrivacyEvidenceRecord.control_reference`, validation service. | Full risk/control/action catalog is approved. | Independent control/evidence/risk stack. |
| DPO/GRC decisions | `PrivacyGovernanceDecisionService`, `PrivacyApprovalRecord`, UI decision actions. | Additional roles or review/advice lifecycle approved. | Duplicate decision endpoints/services. |
| Evidence | `PrivacyEvidenceRecord`, `PrivacyApprovalRecord`, Excel projection, general audit service. | Durable evidence repository approved. | Evidence stored only in workbook or comments. |
| UI | Existing privacy dashboard/case detail/decision components. | Active route/API composition is confirmed. | Second privacy UI or separate governance center. |
| Excel | `PrivacyGovernanceExcelSync` as projection. | Additional projection tabs are approved. | Excel as authoritative input. |
| Auth/RBAC | Existing session/auth dependencies and permission model. | Privacy-specific permissions are approved. | New auth/session system. |
| Analytics | Existing conversation-event privacy validation only where appropriate; Batch 05 event policy. | Product analytics boundary and consent/lawful basis are approved. | Sending raw learner text/conversations as analytics. |

## 12. DO-NOT-BUILD Matrix

| Do not build | Reason |
|---|---|
| A second privacy governance backend. | Existing privacy package and general governance package already exist. |
| A second `decision_router` or duplicate decision API. | `backend/app/api/privacy_governance.py` explicitly says the existing `router` is canonical. |
| A new auth/session architecture. | Authentication cookie/session repository already exists and is out of scope. |
| Consent by reusing authentication state. | Consent and authentication are semantically distinct. |
| Excel-driven governance state. | Excel sync is projection only; registries are authoritative. |
| Full DPIA entity merely because the template exists. | Template structure is not implementation authority; DPIA applicability is legal/DPO decision. |
| FRIA for every EasyChatBot use case by default. | Article 27 applicability must pass classification/applicability gate. |
| Invented TIA methodology. | Transfer legal approach requires legal decision. |
| Processor/recipient collapse. | Existing models distinguish processor facts and recipient fields. |
| Control/evidence collapse. | Evidence may reference controls but is not the control. |
| DPO review as final governance decision. | Review/advice and decision are separate concepts. |
| Analytics payloads containing raw learner conversations, exact text, voice recordings, Telegram content, cookies, tokens, credentials, secrets, or unnecessary identifiers. | Batch 05 forbids by default. |
| New product analytics store without policy/legal decision. | Consent/lawful basis, retention, access, and governance approval are unresolved. |
| Mandatory Google Analytics, third-party consent SDK, Osano runtime, FrenchTeacherAI, or AI runtime redesign. | Explicitly out of scope in previous batches. |
| Refactoring general governance and privacy governance into one system during M0. | Batch 05 conflict rule requires decision first. |

## 13. Conflicts and Ambiguities

| Conflict or ambiguity | Existing authoritative component | Affected contracts/data | STOP or next action |
|---|---|---|---|
| Privacy governance API file declares canonical `/api/privacy/governance` router, but `backend/app/main.py` did not visibly include that router. Tests import/register it directly. | `backend/app/main.py` as active Academy composition root; `backend/app/api/privacy_governance.py` as router file. | Frontend privacy API calls, backend runtime availability, test/runtime parity. | STOP implementation; architecture decision required. |
| General governance center and privacy governance center both exist. | `backend/governance` and `frontend/components/operations-center` for general governance; `backend/app/application/privacy` and `frontend/components/privacy-governance` for privacy. | Change, approval, evidence, dashboard, routes. | STOP merge/refactor; decide bounded-context relationship. |
| Privacy governance state is in-memory while source pack targets governance framework capabilities. | `PrivacyGovernanceComposition` and registries. | Case/approval/evidence durability, auditability, production readiness. | Architecture decision before migrations. |
| Source pack refers to Legal Source Register, but no standalone register file/model found. | Batch 04 `LEGAL_SOURCE_HANDLING.md` only. | Legal provenance, traceability, source versioning. | Legal/governance decision; create docs/register only in later authorized milestone. |
| DPIA screening exists, full DPIA does not. | `DPIAScreeningRegistry` and Batch 04 DPIA template. | Processing activity lifecycle, risk/evidence, DPO review, decision. | DPO/legal decision on applicability; architecture design before entity creation. |
| FRIA template/questionnaire exist, but no repo FRIA implementation found. | Batch 04 FRIA materials. | AI classification, fundamental rights mapping, risk, approvals, monitoring. | Legal classification/applicability gate required. |
| Transfer fields exist, but no approved TIA methodology. | `ProcessorRecord`, `DataProcessingMapEntry`; workbook processor/transfer register. | Transfer safeguards, processor register, legal source map. | Legal decision required; do not invent method. |
| `PrivacyOperationalRegister.add_processing_map()` references attributes (`map_id`, `processing_activity_id`) inconsistent with `DataProcessingMap`, which is a registry keyed by processing ID. | `DataProcessingMapEntry` appears to be the actual map entry; `PrivacyOperationalRegister` may be stale/unused. | Operational register integration if used later. | Architecture/code audit before reuse; do not build on this without verification. |
| `backend/app/application/privacy_governance/processor_registry_service.py` is a separate simple processor registry with `scc_tia`; `backend/app/application/privacy/processor_registry.py` has richer processor model. | Richer `backend/app/application/privacy/processor_registry.py`. | Processor/TIA/transfer mapping. | Consolidation decision; avoid duplicate processor registers. |
| Conversation events store message content, while Batch 05 forbids full learner conversations/exact learner text for analytics by default. | Conversation event storage is learning/conversation history, not generic analytics. | Analytics event policy, learning data, memory pipelines. | Governance/legal decision before analytics reuse; maintain boundary. |
| RBAC permissions only cover announcements in inspected `Permission` enum. | Existing auth/session/RBAC system. | Privacy governance UI/API authorization. | Architecture/security decision before adding privacy permissions. |

## 14. Legal/Architecture Decisions Required

| Decision | Owner likely required | Blocks |
|---|---|---|
| Is `backend/app/api/privacy_governance.py` to be registered in the active app, and under what auth/RBAC dependency? | Architecture/security | Any API/UI integration milestone. |
| Are privacy governance cases/approvals/evidence production features or Beta/demo only? | Architecture/GRC | Persistence/migrations, audit retention. |
| Which component is authoritative for generic governance versus privacy-specific governance? | Architecture/GRC | Reuse/bridge design between `backend/governance` and `backend/app/application/privacy`. |
| What is the authoritative Processing Activity/RoPA source after M0? | DPO/GRC/architecture | Durable registry and workbook sync design. |
| Is a full DPIA required for any EasyChatBot processing activity? | DPO/legal | DPIA implementation and gate behavior. |
| Does AI Act Article 27 apply to EasyChatBot for any use case? | Legal/AI governance | Statutory FRIA implementation. |
| Is a broader internal FRIA required even if Article 27 does not apply? | GRC/legal/AI governance | Internal FRIA lifecycle scope. |
| What transfer mechanisms apply to Telegram/provider/support flows, and is a TIA required? | Legal/DPO | Transfer assessment fields and evidence. |
| What analytics events are approved, with what purpose, legal basis/consent, retention, access, and minimisation? | Legal/DPO/GRC/product | Analytics event boundary and validation. |
| Do privacy governance endpoints require new privacy-specific permissions? | Security/architecture | RBAC extension. |
| Should Legal Source Register be docs-only, code-readable configuration, or persisted domain object? | Legal/GRC/architecture | Source provenance implementation. |

## 15. Smallest Safe Integration Recommendation

Recommended path after four-eyes review:

1. Treat `backend/app/application/privacy` as the privacy governance application boundary.
2. Treat `backend/governance` as the general governance/Operations Center boundary.
3. Do not merge these contexts in code until architecture approves a bridge contract.
4. Use existing `ProcessingActivity`, `DataProcessingMapEntry`, `DPIAScreening`, `ProcessorRecord`, `RetentionRule`, `PrivacyChange`, `PrivacyGovernanceCase`, `PrivacyApprovalRecord`, and `PrivacyEvidenceRecord` as the first mapping targets.
5. Keep Excel one-way: application registry state to workbook projection.
6. Create a Legal Source Register as a later authorized documentation/config artifact before implementing legal-source-backed UI or entities.
7. Add DPIA/FRIA/TIA only as extensions of the existing case/change/evidence/risk/decision model, after legal applicability decisions.
8. Keep consent separate from authentication and analytics separate from learning/conversation events.
9. Resolve route composition and RBAC before any UI/API milestone.
10. Only then consider durable repositories/migrations, preserving existing service contracts.

Smallest safe integration principle:

Extend existing registries/services behind their current interfaces. Do not introduce a second governance state store, second privacy API namespace, second approval engine, second processor registry, or new auth/session layer.

## 16. Proposed Milestone Sequence

| Milestone | Scope | Preconditions | Output |
|---|---|---|---|
| M0 | Discovery only. | Complete source context. | This artifact. |
| M0 Review Gate | Four-eyes review of this artifact. | M0 complete. | Approved/rejected/conditional implementation path. |
| M1 | Architecture decisions and source register. | Decisions on router registration, bounded-context relationship, Legal Source Register ownership. | No production behavior unless approved; docs/config only if authorized. |
| M2 | Repository-backed governance persistence design. | Architecture approves durability and table ownership. | Migration plan, repository contracts, test plan; no migration until separately authorized. |
| M3 | Processing/RoPA/Data Flow/Processor/Retention hardening. | DPO/GRC decide authoritative fields and pending statuses. | Extensions to existing models/services only. |
| M4 | DPIA screening enhancement and DPIA design. | DPO/legal decide DPIA applicability. | Screening-to-DPIA handoff design; full DPIA only if approved. |
| M5 | FRIA applicability gate. | Legal/AI governance decide Article 27 and internal FRIA scope. | FRIA routing/design integrated with existing governance case model. |
| M6 | Transfer/TIA extension. | Legal approves transfer methodology and facts. | Transfer assessment extension without invented TIA scoring. |
| M7 | Consent and analytics boundary. | Legal/DPO/product approve analytics events, lawful basis/consent, retention, access. | Fail-closed analytics validation; no auth-session redesign. |
| M8 | UI/API integration hardening. | Router/RBAC decisions complete. | Existing privacy UI wired to active backend safely. |
| M9 | Monitoring/reassessment/passport/health. | Durable evidence and lifecycle model approved. | Assessment health/passport views derived from existing lifecycle state. |

## Files Inspected

### Source pack

- `BATCH_00_START_HERE/01_READ_FIRST`
- `BATCH_00_START_HERE/ATTACHMENT_ORDER_AND_PROMPT_GUIDE.md`
- `BATCH_00_START_HERE/CODEX_MASTER_INSTRUCTION.md`
- `BATCH_00_START_HERE/SOURCE_PRECEDENCE_AND_STOP_RULES.md`
- `BATCH_01_CONTROLLING_SPECIFICATION/EasyChatBot_Privacy_Governance_Master_Implementation_Specification_v1.1_FINAL.md`
- `BATCH_01_CONTROLLING_SPECIFICATION/EasyChatBot_Privacy_Governance_4_Eyes_Review_v1.0.md`
- `BATCH_02_SEMANTIC_ONTOLOGY/*`
- `BATCH_03_EXISTING_EASYCHATBOT_GOVERNANCE/privacy_governance_tracker.xlsx`
- `BATCH_03_EXISTING_EASYCHATBOT_GOVERNANCE/EasyChatBot_Beta1_Privacy_GRC_DPO_Workbook.xlsx`
- `BATCH_04_LEGAL_REGULATORY_SOURCES/LEGAL_SOURCE_HANDLING.md`
- `BATCH_04_LEGAL_REGULATORY_SOURCES/EDPB_DPIA_Template_2026_Second_DPO_Review_Comments.docx`
- `BATCH_04_LEGAL_REGULATORY_SOURCES/FRIA_Template_EU_AI_Act_Regulator_Ready.docx`
- `BATCH_04_LEGAL_REGULATORY_SOURCES/FRIA_questionnaire.xlsx`
- `BATCH_05_IMPLEMENTATION_RULES_AND_M0/BATCH_README.md`
- `BATCH_05_IMPLEMENTATION_RULES_AND_M0/M0_ACCEPTANCE_GATE.md`
- `BATCH_05_IMPLEMENTATION_RULES_AND_M0/REPOSITORY_CONFLICT_RULE.md`
- `BATCH_05_IMPLEMENTATION_RULES_AND_M0/ANALYTICS_EVENT_DATA_POLICY.md`

### Repository source and docs

- `backend/app/main.py`
- `backend/api/main.py`
- `run_backend.py`
- `run_server.py`
- `backend/app/api/privacy_governance.py`
- `backend/app/api/authentication.py`
- `backend/app/api/dependencies/identity.py`
- `backend/app/api/dependencies/authorization.py`
- `backend/app/domain/authorization/permissions.py`
- `backend/app/application/privacy/README.md`
- `backend/app/application/privacy/processing_activity.py`
- `backend/app/application/privacy/processing_activity_record.py`
- `backend/app/application/privacy/processing_registry.py`
- `backend/app/application/privacy/data_processing_map.py`
- `backend/app/application/privacy/retention_registry.py`
- `backend/app/application/privacy/retention_classification.py`
- `backend/app/application/privacy/processor_registry.py`
- `backend/app/application/privacy/dpia_screening.py`
- `backend/app/application/privacy/privacy_validation_service.py`
- `backend/app/application/privacy/privacy_change.py`
- `backend/app/application/privacy/privacy_change_detector.py`
- `backend/app/application/privacy/privacy_change_assessment.py`
- `backend/app/application/privacy/privacy_change_registry.py`
- `backend/app/application/privacy/privacy_governance_gate.py`
- `backend/app/application/privacy/privacy_governance_flow_service.py`
- `backend/app/application/privacy/privacy_governance_case.py`
- `backend/app/application/privacy/privacy_governance_case_service.py`
- `backend/app/application/privacy/privacy_governance_case_registry.py`
- `backend/app/application/privacy/privacy_governance_decision_service.py`
- `backend/app/application/privacy/privacy_approval_record.py`
- `backend/app/application/privacy/privacy_approval_registry.py`
- `backend/app/application/privacy/privacy_evidence_record.py`
- `backend/app/application/privacy/privacy_governance_dashboard_service.py`
- `backend/app/application/privacy/privacy_governance_dashboard_api.py`
- `backend/app/application/privacy/privacy_governance_composition.py`
- `backend/app/application/privacy/privacy_governance_excel_sync.py`
- `backend/app/application/privacy/privacy_governance_tracker_projection.py`
- `backend/app/application/privacy/privacy_governance_tracker_config.py`
- `backend/app/application/privacy/privacy_identifier_service.py`
- `backend/app/application/privacy_governance/processor_registry_service.py`
- `backend/app/application/privacy_governance/ropa_engine.py`
- `backend/app/application/privacy_governance/deletion_workflow_service.py`
- `backend/app/application/privacy_governance/anonymisation_pipeline_service.py`
- `backend/app/application/conversation/conversation_event_models.py`
- `backend/app/application/conversation/conversation_event_repository.py`
- `backend/app/application/conversation/privacy.py`
- `backend/app/application/conversation_quality/conversation_event_validator.py`
- `backend/app/infrastructure/persistence/conversation_event_records.py`
- `backend/app/infrastructure/persistence/postgresql_conversation_event_repository.py`
- `backend/app/infrastructure/persistence/database.py`
- `backend/app/infrastructure/auth/session_identity_provider.py`
- `backend/app/infrastructure/auth/postgresql_auth_repository.py`
- `backend/governance/change_management/*`
- `backend/governance/approval/*`
- `backend/governance/governance_audit_service.py`
- `backend/governance/operations_center/*`
- `backend/governance/api/*`
- `backend/alembic/versions/*` schema sweep
- `backend/migrations/001_beta_telegram_access.sql`
- `frontend/lib/privacy-governance/*`
- `frontend/components/privacy-governance/*`
- `frontend/app/privacy-governance/page.tsx`
- `frontend/components/operations-center/README_GOVERNANCE_CENTER.md`
- `docs/privacy-governance/governance-architecture.md`
- `docs/privacy-governance/privacy-governance-api-contract.md`
- `docs/privacy-governance/phase-6-acceptance-criteria.md`
- `docs/privacy/ROPA.md`
- `docs/privacy/AI_Data_Governance.md`
- `docs/privacy/Deletion_Workflow.md`
- `docs/privacy/beta1/DPO_GRC_Legal_Signoff.md`
- `docs/privacy/beta1/EasyChatBot_Beta1_Privacy_GRC_DPO_Workbook.xlsx`
- `docs/governance/privacy/EasyChatBot_Privacy_Governance_Framework_DPO_Package/*`

## End-State M0 Summary

### Key findings

- A privacy governance implementation already exists and must be reused.
- DPIA screening exists; full DPIA does not.
- FRIA does not exist in active source paths.
- Transfer facts exist; TIA methodology does not.
- Excel governance tracker is a projection, not source of truth.
- Legal Source Register is missing/pending.
- Privacy governance persistence is in-memory; no privacy governance tables found.
- Privacy UI exists, but API composition and routing require verification.
- Consent management was not found; authentication exists and must stay separate.
- Conversation events exist and include content, so they must not be treated as generic analytics under Batch 05.

### Proposed reuse

Reuse the existing privacy package, decision service, case service, validation service, data map, processor registry, DPIA screening registry, evidence records, dashboard projection, Excel sync projection, auth/session layer, and existing UI components.

### Proposed changes after M0 review only

- Resolve router registration and RBAC.
- Establish Legal Source Register.
- Decide durable repository strategy.
- Extend existing models for DPIA/FRIA/TIA only after legal applicability decisions.
- Add analytics policy validation only after lawful basis/consent/retention/access decisions.

### Conflicts

- Privacy API router existence versus active app registration.
- General governance versus privacy governance bounded contexts.
- In-memory governance state versus production governance durability expectations.
- Conversation event content versus analytics prohibition by default.
- Duplicate/legacy processor registry surface.

### Decisions required

Architecture, DPO/GRC, legal, AI governance, and security decisions listed in Section 14 are required before implementation.

### Explicit DO-NOT-BUILD items

The DO-NOT-BUILD matrix in Section 12 is controlling for post-M0 implementation planning unless superseded by approved architecture/legal decisions.

