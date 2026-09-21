# PI-1B Build Package — Installation Order

Canonical repository:

`C:\AI Folder\ai_agents`

## Phase A — additive files

1. Copy `runtime/agents/services/skill_execution_service.py`.
2. Copy `prompt_builder/builders/platform_intelligence_prompt_builder.py`.
3. Copy the accompanying unit tests.

## Phase B — Skill resource resolution

Apply a safe `SkillLoader.load_prompt()` implementation to the canonical
SkillLoader.

Requirements:
- resolve the prompt reference relative to the Skill directory;
- reject absolute prompt paths;
- reject path traversal outside the Skill directory;
- require a regular file;
- read UTF-8 text;
- reject empty prompt resources.

## Phase C — composition

The active workstream has introduced:
- `platform_intelligence` prompt builder registration;
- per-agent execution-service composition;
- Platform Intelligence-specific execution boundary.

Verify these against the local repository before applying additional edits.

## Phase D — PI agent

Wire the PI agent to:
1. build `InvestigationRequest`;
2. build `InvestigationPlan`;
3. select a Runtime-authorised Skill;
4. execute through `SkillExecutionService`;
5. create evidence only from actual evidence-producing Skills;
6. create `OutputAssessment`;
7. return `InvestigationResult`.

Until an evidence-producing Skill exists, confidence must not be HIGH merely
because an LLM generated an answer.

## Validation

Formatting → lint → type check → focused tests → runtime regression →
integration → security → build → smoke → review → 4-eyes sign-off.

## Rollback

Back up every existing repository file before replacement. Never overwrite
unrelated working functionality.
