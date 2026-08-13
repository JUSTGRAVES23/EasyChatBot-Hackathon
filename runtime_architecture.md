EasyChatBot Runtime Architecture

1. Purpose

This document defines the current architecture and responsibility boundaries of theEasyChatBot Runtime.

The Runtime is the provider-independent execution layer between an externalapplication/integration boundary and the EasyChatBot Agent framework.

The Runtime must remain independently usable by different application andhackathon workstreams.

2. Architectural Boundary

Current validated flow:

External Application / Integration
              |
              v
     ExternalRuntimeService
              |
              v
        RuntimeEngine
              |
              v
           Agent
              |
              v
           Skills
              |
              v
     Provider Abstraction
              |
              v
       Provider Adapter
              |
              v
       External Provider

The external integration boundary is implemented by:

backend/services/external_runtime_service.py

The Runtime execution engine is implemented by:

backend/runtime/runtime_engine.py

The execution context is defined by:

backend/runtime/context/execution_context.py

3. Validated Runtime Components

Runtime Engine

RuntimeEngine is responsible for controlled execution of an Agent using anExecutionContext.

It returns the standard AgentResult contract.

The Runtime does not own application-specific user experience logic.

Execution Context

ExecutionContext carries the explicit information required for an execution.

Agents receive the context rather than obtaining execution state throughuncontrolled global access.

Agent Contract

Agents implement the standard Agent execution contract and return AgentResult.

The Runtime invokes Agents rather than allowing an external application todirectly orchestrate individual Agent internals.

Skill Contract

Skills are bounded capabilities executed by Agents.

Skills receive explicit SkillInput and return SkillResult.

Skills do not become autonomous execution runtimes.

Provider Contract

Providers implement the provider abstraction.

The Runtime and Agent architecture should depend on provider contracts ratherthan provider SDK implementations.

4. External Runtime Service

The existing external boundary is:

backend/services/external_runtime_service.py

Its architectural role is to provide a controlled application-facing entry pointinto the Runtime.

The validated test coverage includes:

tests/application/test_external_runtime_composition.py
tests/application/test_external_runtime_service.py

Current validation:

test_external_runtime_composition.py  -> 2 passed
test_external_runtime_service.py      -> 3 passed

Therefore the external composition boundary is already an implemented andtested capability. A second Runtime/Application architecture should not becreated for this purpose.

5. Agent Layer

Agents remain responsible for bounded domain execution.

Examples currently present include:

backend/agents/base_agent.py
backend/agents/discovery/discovery_agent.py
backend/agents/research_agent.py
backend/agents/conversation_agent.py
backend/agents/quality_agent.py

The Runtime owns execution orchestration.

Agents own their bounded domain workflow.

This separation must be preserved.

6. Provider Independence

The intended dependency direction is:

Runtime
   |
   v
Agent
   |
   v
Provider Contract
   |
   v
Provider Implementation
   |
   v
External Provider

The Runtime must not directly import or call provider SDKs.

The Parallel integration belongs behind the provider/gateway boundaries and mustnot become Runtime orchestration logic.

7. Current Provider Independence Check

The repository search was performed against:

backend/runtime/**/*.py

The search found one occurrence:

backend/runtime/models/model_id.py
line 19
gemini-2.5-flash

This occurrence is a model identifier in the Runtime model-ID/configuration area.It is not, by itself, evidence that the Runtime imports or calls the Gemini SDK.

Therefore it should NOT be removed merely to satisfy a textual provider search.

The architectural rule is:

Runtime may represent approved model identifiers/configuration.

Runtime must not directly depend on provider SDK implementations.

A future implementation review should distinguish:

model identifiers/configuration;

provider SDK imports;

provider execution calls.

Only the latter two represent direct provider coupling.

8. Parallel Challenge Workstream Boundary

The Parallel challenge workstream and the EasyChatBot Runtime workstream areseparate but compatible.

Runtime Platform Workstream

Owns:

RuntimeEngine
ExecutionContext
Agent contracts
Skill contracts
Provider contracts
Runtime governance
Runtime testing

Parallel / Hackathon Workstream

Owns the challenge-specific integration and demonstration experience.

The workstreams connect through stable application/runtime contracts rather thanby embedding challenge-specific provider logic into the Runtime.

Target relationship:

Parallel / Hackathon Application
              |
              v
     ExternalRuntimeService
              |
              v
       EasyChatBot Runtime

The two workstreams may therefore progress independently.

9. Google Cloud / Gemini Boundary

Google Cloud and Gemini integrations must not be embedded directly into thecore Runtime merely to satisfy an external execution requirement.

The preferred integration boundary is:

Google Cloud / Gemini Integration
              |
              v
     External Runtime Boundary
              |
              v
        EasyChatBot Runtime

This preserves provider independence and allows the Runtime to remain reusable.

Any future Gemini-specific adapter must be reviewed separately for:

authentication;

configuration;

dependency direction;

error handling;

observability;

security;

testability;

provider replacement.

10. Security and Governance Principles

The Runtime architecture must preserve:

explicit execution boundaries;

least-privilege provider access;

controlled external side effects;

explicit Agent and Skill contracts;

no uncontrolled Agent actions;

provider abstraction;

auditable execution;

configuration-driven behaviour where appropriate.

Agents and Skills must not bypass the Runtime to perform uncontrolled productionchanges.

11. Testing Strategy

Runtime changes should follow:

Unit Tests
    |
    v
Contract Tests
    |
    v
Integration Tests
    |
    v
External Composition Tests
    |
    v
Smoke / Runtime Validation

The existing external composition and external runtime service tests are part ofthe Runtime boundary validation.

No new duplicate Runtime composition layer should be introduced while theseexisting boundaries remain valid.

12. Architecture Freeze Decision

For the current Beta/Hackathon integration phase:

Keep

ExternalRuntimeService
RuntimeEngine
ExecutionContext
AgentResult
BaseAgent
Skill
SkillResult
BaseProvider
Parallel Provider/Gateway boundaries

Do not introduce

A second Runtime engine
A second external application/runtime boundary
Direct Parallel SDK usage inside Runtime
Direct Gemini SDK usage inside Runtime
Direct provider SDK usage inside Agents

Integration principle

External Integration
        |
        v
ExternalRuntimeService
        |
        v
RuntimeEngine
        |
        v
Agents
        |
        v
Provider Contracts
        |
        v
Provider Implementations

This is the architectural baseline for subsequent work.

13. Definition of Done for Runtime Architecture Freeze

The Runtime architecture is considered frozen when:

the existing external composition tests pass;

the external runtime service tests pass;

Runtime-to-Agent execution remains contract-based;

Runtime does not directly call provider SDKs;

Parallel remains behind its provider/gateway boundary;

Google/Gemini integration has a defined external integration boundary;

the two development workstreams can evolve independently;

architectural changes are documented before implementation.
