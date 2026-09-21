# PI-1B — Governed Skill Execution Architecture

## Target

PlatformIntelligenceAgent
→ SkillExecutionService
→ SkillRegistry / SkillLoader
→ SkillManifest + Skill resource
→ authorization/compatibility
→ RuntimeContext
→ AgentExecutionService
→ RuntimePromptBuilder
→ platform_intelligence builder
→ ProviderRuntime

## Boundaries

### PlatformIntelligenceAgent
Owns investigation request, plan, reasoning orchestration and result assembly.
It does not call provider SDKs, access databases/filesystems directly, or
perform external actions.

### SkillExecutionService
Owns Skill resolution, active-status validation, compatibility/authorization,
execution metadata and delegation. It does not implement providers or perform
uncontrolled filesystem/external operations.

### SkillLoader
Owns persisted Skill manifest and safe Skill resource loading.

### RuntimePromptBuilder
Owns prompt-builder resolution and prompt lifecycle.

### AgentExecutionService
Owns prompt generation, ProviderRuntime invocation and response normalization.

### ProviderRuntime
Owns provider-independent provider execution.

## Security

The first PI slice is read-only. A Skill cannot gain authority because a
model requests it. Authorization is Runtime policy plus manifest compatibility.

## Confidence

Confidence means support from available information. It is not model certainty,
truth probability, or approval.

No evidence must not produce HIGH confidence. Evidence authority and confidence
are separate dimensions.
