# EasyChatBot — Platform Intelligence Build Package

## Purpose

This package advances the Platform Intelligence (PI) workstream from PI-1A
Skill Infrastructure into PI-1B Governed Skill Execution.

This is an additive build package. It does not replace the canonical Runtime,
Provider, AgentFactory, or existing Project Manager execution path.

## Current project position

- PI-1A Skill infrastructure: GREEN
- Runtime unit suite: GREEN (per project execution results)
- AgentFactory: generic and future-agent ready
- Prompt composition: RuntimePromptBuilder with registered builders
- PI prompt builder: implemented and syntax-checked in the active workstream
- Per-agent execution-service composition: implemented and regression-tested
- PI-1B governed Skill execution: IN PROGRESS
- Evidence-producing/retrieval Skills: NOT YET IMPLEMENTED
- Deep Dive investigation: NOT YET COMPLETE
- Screen/page intelligence: NOT YET COMPLETE
- Escalation workflow: NOT YET COMPLETE

## Delivery status

This ZIP is a build package, not a claim that these files have already been
merged into the user's local repository. The canonical repository is
`C:\AI Folder\ai_agents`.

Apply the package incrementally, preserving local changes. Run the project's
own regression suite after each integration step.

## Architecture guardrails

1. Keep `AgentFactory` generic.
2. Keep provider independence.
3. Keep `AgentExecutionService` as the provider-facing application boundary.
4. Keep Skill governance in Runtime.
5. Keep Skill resources behind the Skill loading boundary.
6. Keep Platform Intelligence read-only in this phase.
7. Never fabricate evidence, source dates, authority, or confidence.
8. Do not add a vector database/RAG platform before direct governed search
   demonstrates a real need.
9. Do not create another AI Runtime.
10. No autonomous production side effects.
