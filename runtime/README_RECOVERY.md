# PI-1B Runtime Recovery Package

This package restores only the missing canonical runtime foundation identified
during repository inspection.

Included:
- `runtime.core.RuntimeContext`
- agent execution request/response contracts
- `AgentExecutionService`

Important:
1. This is a recovery implementation, not a claim that these files existed
   in Git history. Repository inspection found no committed RuntimeContext.
2. Do not overwrite existing runtime files with this package.
3. Before applying, compare imports and tests against the current repository.
4. The existing provider boundary remains authoritative.
5. Run targeted PI-1B tests before any broader feature work.

Known compatibility requirement:
existing tests construct RuntimeContext with `model_construct(...)`, so the
fields represented here preserve that surviving contract.
