# Step 16 Change Manifest

## CREATE — provisional files in this package

- `src/ai_agents/internal_documentation_agent/models.py`
- `src/ai_agents/internal_documentation_agent/knowledge_provider.py`
- `src/ai_agents/internal_documentation_agent/agent.py`
- `src/ai_agents/internal_documentation_agent/composition.py`
- `src/ai_runtime/capabilities/internal_documentation_executor.py`
- corresponding tests

## MODIFY — only after WP16.1 confirms exact repository contracts

- existing CapabilityType definition
- existing Capability Registry
- existing Capability Gateway wiring
- canonical application composition/bootstrap
- existing governance/authorization configuration
- existing Project Brain/Knowledge implementation

## REUSE

- existing Runtime
- existing Capability Gateway
- existing Agent conventions
- existing governance
- existing testing infrastructure
- existing Project Brain/Knowledge implementation if present

## DO NOT TOUCH

- unrelated Live Intelligence functionality
- unrelated provider implementations
- legacy Runtime generations unless proven necessary
- unrelated application features
- unrelated dependencies
