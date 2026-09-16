# Repository Integration Required

The package intentionally does not fabricate the existing repository's exact registry/bootstrap contracts.

Before merging these files:

1. Inspect the current `CapabilityType`.
2. Add/reuse `INTERNAL_DOCUMENTATION_SEARCH` following the existing enum/model convention.
3. Register the executor in the existing Capability Registry.
4. Wire the executor through the existing Capability Gateway.
5. Wire the KnowledgeProvider to the existing Project Brain/internal knowledge implementation.
6. Wire the agent through the canonical composition root.
7. Add the capability authorization policy using the existing governance mechanism.
8. Add integration/E2E tests using the repository's real gateway/bootstrap path.

DO NOT:
- create a second CapabilityGateway;
- create a second Runtime;
- connect the Agent directly to Parallel/Gemini/OpenAI/Ollama;
- bypass application/runtime authorization;
- introduce a second knowledge abstraction if the repository already has one.
