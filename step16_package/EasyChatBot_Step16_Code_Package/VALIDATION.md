# Validation

Activate the repository .venv first.

Run repository-configured formatter/linter/type checker.

Targeted:
pytest -q tests/unit/ai_agents/internal_documentation_agent
pytest -q tests/unit/ai_runtime/test_internal_documentation_executor.py
pytest -q tests/security/test_internal_documentation_boundary.py

Then run the relevant Runtime/application integration tests.

Finally:
pytest -q

Treat unrelated existing collection failures separately and document them.
Do not weaken tests to obtain a green result.
