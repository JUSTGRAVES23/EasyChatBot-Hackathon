EasyChatBot Runtime Boundaries

Purpose

This document records the approved separation between the EasyChatBot application,the external/user-assistance AI Runtime, the internal AI Agents framework, thelower-level backend Runtime, capabilities, and providers.

The purpose is to prevent the two Runtime concepts from being treated as duplicatesystems and to preserve the architecture while the Parallel challenge workstreamand the platform Runtime workstream develop in parallel.

1. High-Level Architecture

The current architecture is:

FastAPI Application
        |
        v
ExternalRuntimeService
        |
        v
External / User-Assistance AI Runtime
(src/ai_runtime)
        |
        v
CapabilityGateway
        |
        v
CapabilityRegistry
        |
        v
CapabilityExecutor
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

The existing backend/runtime layer remains a separate lower-level Runtimefoundation.

2. Application Layer

Primary locations:

backend/api/
backend/services/
backend/application/

Responsibilities:

expose application/API entry points;

validate application requests;

compose approved services and dependencies;

delegate Runtime execution;

return application-facing responses.

The API layer must not contain:

Agent business logic;

Skill execution logic;

provider SDK calls;

direct Parallel Search orchestration;

direct Gemini orchestration;

independent Runtime logic.

The existing FastAPI application is the application boundary.

3. External / User-Assistance AI Runtime

Primary location:

src/ai_runtime/

The external AI Runtime is the application-facing controlled capability runtime.

Its composition root is:

src/ai_runtime/composition.py

The composition layer wires together:

Governance
    |
    v
CapabilityGateway
    |
    v
CapabilityRegistry
    |
    +--> Live Intelligence
    +--> Podcast Discovery
    +--> Learning Generation
    +--> Podcast Listening Proposal

The composition root is responsible for dependency injection.

It must not:

implement capability business logic;

implement provider logic;

retrieve learner memory;

make governance decisions itself;

execute Agents directly;

perform external side effects;

modify the internal AI Agents framework.

4. Capability Layer

Primary location:

src/ai_runtime/capabilities/

Capabilities are the approved execution surfaces exposed through the externalRuntime.

Current examples include:

LiveIntelligenceExecutor
PodcastDiscoveryExecutor
PodcastLearningChallengeExecutor
ListeningProposalExecutor

The capability layer:

receives controlled Runtime requests;

delegates to approved executors/Agents;

remains behind the CapabilityGateway;

does not become a second Agent framework.

Governance remains at the CapabilityGateway boundary.

5. Internal AI Agents Framework

The internal AI Agents framework is a separate system.

It must not be merged with the external/user-assistance Runtime.

Its responsibility is Agent execution and related Agent framework concerns.

The external Runtime may invoke approved Agent-backed capabilities, but it mustnot modify or replace the internal Agent framework.

Conceptually:

External AI Runtime
        |
        v
Approved Capability
        |
        v
Internal Agent
        |
        v
Agent Execution

This separation is intentional.

6. backend/runtime

Primary location:

backend/runtime/

This is the lower-level Runtime foundation.

Validated components include:

backend/runtime/runtime_engine.py
backend/runtime/context/execution_context.py
backend/runtime/models/

The Runtime foundation provides execution contracts and controlled Agent execution.

It remains provider-independent.

The Runtime must not directly import provider SDKs.

Provider-specific integrations remain behind provider contracts and providerimplementations.

7. Relationship Between the Two Runtime Concepts

The two Runtime concepts are complementary rather than duplicate.

External / User-Assistance Runtime

src/ai_runtime

Focus:

application-facing capabilities;

capability registration;

governance boundary;

controlled user-assistance execution.

Backend Runtime

backend/runtime

Focus:

lower-level execution foundation;

ExecutionContext;

RuntimeEngine;

Agent execution contracts;

provider-independent Runtime behaviour.

The architecture must not collapse these into one implementation merely becauseboth contain the word "Runtime".

8. Application-to-Runtime Flow

The approved application flow is:

User / Hackathon Application
            |
            v
        FastAPI API
            |
            v
 ExternalRuntimeService
            |
            v
      CapabilityGateway
            |
            v
      CapabilityRegistry
            |
            v
    Capability Executor
            |
            v
           Agent
            |
            v
          Skills
            |
            v
    Provider Contract
            |
            v
 Provider Implementation
            |
            v
     External Provider

The exact lower-level composition may vary by capability, but the responsibilityboundaries must remain intact.

9. Parallel Challenge Workstream

The Parallel challenge is a separate workstream from the Runtime platform workstream.

The workstreams must remain independently developable and mutually compatible.

Runtime platform workstream

Owns:

backend/runtime/
backend/agents/
backend/skills/
backend/providers/
backend/services/external/

Parallel challenge workstream

Owns challenge-specific:

Parallel Search integration
hackathon application flow
demonstration experience
Google Cloud integration/deployment
Gemini integration where required

The Parallel challenge must connect through approved application, capability,gateway, and provider boundaries.

It must not introduce a second Runtime.

10. Parallel Search Boundary

Parallel Search must remain behind its provider/gateway boundary.

Preferred flow:

Capability / Agent
        |
        v
Discovery Skill
        |
        v
Discovery Gateway
        |
        v
Parallel Provider
        |
        v
Parallel Search API

The Discovery Skill must not directly depend on the Parallel SDK.

The Runtime must not directly depend on the Parallel SDK.

11. Gemini Boundary

Gemini must follow the same provider-independent architecture.

Preferred flow:

Capability / Agent
        |
        v
LLM Provider Contract
        |
        v
Gemini Provider
        |
        v
Google Cloud / Gemini

Gemini SDK dependencies must remain in the provider implementation layer.

The following must not be introduced merely for Gemini:

backend/runtime/gemini/
backend/runtime/google_client.py
backend/agents/gemini_agent.py

The existing LLM provider abstraction and factory are the approved extensionpoints.

12. Google Cloud Boundary

Google Cloud should host the existing application boundary rather than introducea separate Runtime implementation.

Approved conceptual deployment:

Google Cloud
      |
      v
FastAPI Application
      |
      v
ExternalRuntimeService
      |
      v
External AI Runtime
      |
      v
Capabilities

Google Cloud deployment concerns must remain separate from Runtime businesslogic.

13. Governance Boundary

Governance is injected at the external Runtime composition boundary.

Conceptually:

Application Composition
        |
        v
CapabilityGateway
        |
        +--> Governance
        |
        v
CapabilityRegistry

Capability executors must not independently create a competing governanceframework.

The Runtime must preserve explicit governance and control boundaries.

14. Provider Independence

Provider independence is a core architectural requirement.

The dependency direction is:

Application
    |
    v
Runtime / Capability
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

The following direct dependencies are prohibited in the core Runtime and Agentlayers:

Parallel SDK
Gemini SDK
Google SDK
OpenAI SDK
Anthropic SDK

Provider-specific code belongs in provider implementations.

17. Approved Target for the Parallel Challenge

The challenge integration should ultimately demonstrate:

User
 |
 v
FastAPI / Web Application
 |
 v
ExternalRuntimeService
 |
 v
CapabilityGateway
 |
 v
Discovery Capability
 |
 v
Discovery Agent
 |
 +----------------------+
 |                      |
 v                      v
Parallel Search       Gemini
(retrieval)           (AI processing)
 |
 +----------+-----------+
            |
            v
       Verified Result
            |
            v
      User-facing Output

This is the target integration shape.

It does not require redesigning the existing Runtime.

18. Architecture Freeze Decision

The current architecture is approved for Sprint 1 implementation.

The next work should focus on the Parallel challenge vertical slice rather thancreating additional Runtime architecture.

Any proposed architectural change must demonstrate a concrete requirement thatcannot be satisfied through the existing boundaries.